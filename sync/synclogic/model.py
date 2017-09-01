
import base64
from collections import OrderedDict
import contextlib
import datetime
import hashlib
import json
import logging
import psycopg2
import psycopg2.extras
import struct
import time
import uuid
psycopg2.extras.register_uuid()
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

log  = logging.getLogger(__name__)

# publiclog, serieslog, mergeservers and mergepasswords are used during merging but are never merged themselves
# results can be generated from tables so there is no need to merge it

TABLE_ORDER = [
    'drivers',
    'timertimes',
    'settings',
    'indexlist',
    'events',   
    'classlist',
    'classorder',
    'cars',
    'registered',
    'runorder',
    'runs',
    'challenges',
    'challengerounds',
    'challengeruns',
]

COLUMNS       = dict()
PRIMARY_KEYS  = dict()
NONPRIMARY    = dict()
HASH_COMMANDS = dict()

LOCALARGS = {
  "cursor_factory": psycopg2.extras.DictCursor,
            "host": "/var/run/postgresql",
            #"host": "127.0.0.1", "port": 6432,
            "user": "postgres",  # Need to be able to create users, schema, etc.
          "dbname": "scorekeeper",
"application_name": "synclocal"
}

REMOTEARGS = {
  "cursor_factory": psycopg2.extras.DictCursor,
            "port": 54329,
          "dbname": "scorekeeper",
"application_name": "syncremote",
   # Must specify host, user and password
}

def initialize():
    """ A little introspection to load the schema from database so we don't have to keep a local copy in this file """
    with DataInterface.connectLocal() as db:
        with db.cursor() as cur:
            # Need to set a valid series so we can inspect the format
            cur.execute("SELECT schema_name FROM information_schema.schemata")
            serieslist = set([x[0] for x in cur.fetchall() if not x[0].startswith('pg_') and x[0] not in ('information_schema', 'public')])
            if not len(serieslist):
                return False

            cur.execute("set search_path=%s,%s", (serieslist.pop(), 'public'))

            # Determing the primary keys for each table
            for table in TABLE_ORDER:
                cur.execute("SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)" \
                            "WHERE i.indrelid = '{}'::regclass AND i.indisprimary".format(table))
                PRIMARY_KEYS[table] = [row[0] for row in cur.fetchall()]

                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='{}'".format(table))
                COLUMNS[table] = [row[0] for row in cur.fetchall()]
                NONPRIMARY[table] = list(set(COLUMNS[table]) - set(PRIMARY_KEYS[table]))

    SUMPART = "sum(('x' || substring(t.rowhash, {}, 8))::bit(32)::bigint)"
    SUMS = "{}, {}, {}, {}".format(SUMPART.format(1), SUMPART.format(9), SUMPART.format(17), SUMPART.format(25))
    for table, pk in PRIMARY_KEYS.items():
        md5cols = '||'.join("md5({}::text)".format(k) for k in pk+['modified'])
        HASH_COMMANDS[table] = "SELECT {} FROM (SELECT MD5({}) as rowhash from {}) as t".format(SUMS, md5cols, table)

    return True


class DataInterface(object):

    @classmethod
    def connectLocal(cls):
        return psycopg2.connect(**LOCALARGS)

    @classmethod
    def connectRemote(cls, host, user, password):
        return psycopg2.connect(host=host, user=user, password=password, **REMOTEARGS)

    @classmethod
    def loadPasswords(cls, db):
        ret = dict()
        with db.cursor() as cur:
            cur.execute("SELECT * FROM pg_shadow WHERE passwd NOT LIKE 'md5%'")
            for row in cur.fetchall():
                ret[row['usename']] = row['passwd']
        return ret

    @classmethod
    def insert(cls, db, objs):
        if len(objs) == 0: return
        stmt = "INSERT INTO {} ({}) VALUES ({})".format(objs[0].table, ",".join(COLUMNS[objs[0].table]), ",".join(["%({})s".format(x) for x in COLUMNS[objs[0].table]]))
        with db.cursor() as cur:
            for obj in objs:
                cur.execute(stmt, obj.data)

    @classmethod
    def update(cls, db, objs):
        if len(objs) == 0: return
        stmt = "UPDATE {} SET {} WHERE {}".format(objs[0].table, ", ".join("{}=%({})s".format(k,k) for k in NONPRIMARY[objs[0].table]), " AND ".join("{}=%({})s".format(k, k) for k in PRIMARY_KEYS[objs[0].table]))
        with db.cursor() as cur:
            for obj in objs:
                cur.execute(stmt, obj.data)

    @classmethod
    def delete(cls, db, objs):
        """
            Delete as well as fix up log as delete trigger has no timestamp to reference and therefore defaults to CURRENT_TIMESTAMP 
            which is correct in the local access case but wrong in the merge case
        """
        if len(objs) == 0: return
        stmt = "DELETE FROM {} WHERE {}".format(objs[0].table, " AND ".join("{}=%({})s".format(k,k) for k in PRIMARY_KEYS[objs[0].table]))
        logu = "UPDATE {} SET time=%s WHERE time=CURRENT_TIMESTAMP".format((objs[0].table=='drivers') and 'publiclog' or 'serieslog')
        with db.cursor() as cur:
            for obj in objs:
                cur.execute(stmt, obj.data)
                cur.execute(logu, (obj.deletedat,))

    @classmethod
    def copyTable(cls, srcdb, dstdb, series, table):
        """ Use psycopg2 execute_values to perhaps insert data a little faster """
        log.debug("copy table %s/%s", series, table)
        with srcdb.cursor() as scur, dstdb.cursor() as dcur:
            istmt = "INSERT INTO {} ({}) VALUES %s".format(table, ",".join(COLUMNS[table]))
            templ = "({})".format(",".join(["%({})s".format(x) for x in COLUMNS[table]]))
            scur.execute("set search_path=%s,%s", (series, 'public'))
            dcur.execute("set search_path=%s,%s", (series, 'public'))
            scur.execute("select * from {}".format(table))
            psycopg2.extras.execute_values(dcur, istmt, scur.fetchall(), templ)

    @classmethod
    @contextlib.contextmanager
    def mergelocks(cls, local, localdb, remote, remotedb):
        """
            Context manager to acquire/release advisory locks on both servers.
            It will throw assertion error if it can't get both.  The logic for
            first lock to obtain is there to help dynamic merging systems in
            obtaining locks in the same order to reduce distributed lock race
            conditions.  The current order is lower serverid first.
            Also sets replication role to local which signals our triggers to
            not log changes as we need to create the log entries ourselves.
        """
        lock1 = False
        lock2 = False
        try:
            if local.serverid < remote.serverid:
                cur1 = localdb.cursor()
                cur2 = remotedb.cursor()
            else:
                cur1 = remotedb.cursor()
                cur2 = localdb.cursor()
            
            cur1.execute("SELECT pg_try_advisory_lock(42)")
            lock1 = cur1.fetchone()[0]
            if lock1:
                cur2.execute("SELECT pg_try_advisory_lock(42)")
                lock2 = cur2.fetchone()[0]
            assert lock1 and lock2, "Unable to obtain both locks, will try again later"
            log.debug("Acquired both locks")
            yield
        finally:
            log.debug("Releasing locks (%s, %s)", lock1, lock2)
            if lock2:
                cur2.execute("SELECT pg_advisory_unlock(42)")
                cur2.close()
            if lock1:
                cur1.execute("SELECT pg_advisory_unlock(42)")
                cur1.close()


class PresentObject():

    def __init__(self, table, pk, data):
        self.table = table
        self.pk = pk
        self.data = data
        self.modified = data['modified']

    @classmethod
    def minmodtime(cls, d):
        if len(d) == 0:
            return datetime.datetime(2017, 1, 1)
        return min([v.modified for v in d.values()])

    @classmethod
    def loadPresent(cls, db, table):
        assert table in TABLE_ORDER, "No such table {}".format(table)
        ret = dict()
        with db.cursor() as cur:
            cur.execute("SELECT * from {}".format(table))
            for row in cur.fetchall():
                pk = tuple([row[k] for k in PRIMARY_KEYS[table]])
                ret[pk] = cls(table, pk, row)
        return ret


# For storage and query of recently deleted objects
class DeletedObject():

    def __init__(self, table, pk, data, deletedat):
        self.table = table
        self.pk = pk
        self.data = data
        self.deletedat = deletedat

    @classmethod
    def deletedSince(cls, db, table, when):
        assert table in TABLE_ORDER, "No such table {}".format(table)
        ret = dict()
    
        def lift_value(v):
            """ Lift string UUIDs from JSON back into UUIDs for comparison """
            if type(v) is str:
                try: return uuid.UUID(v)
                except: pass
            return v

        with db.cursor() as cur:
            log = (table=='drivers') and 'publiclog' or 'serieslog';
            cur.execute("SELECT time, olddata FROM {} WHERE action='D' AND tablen=%s AND time>%s".format(log), (table, when,))
            for row in cur.fetchall():
                pk = tuple([lift_value(row['olddata'][k]) for k in PRIMARY_KEYS[table]])
                ret[pk] = cls(table, pk, row['olddata'], row['time'])
        return ret


# For storage of server information 
class MergeServer(object):

    def __init__(self, nt, db):
        self.db = db
        for k,v in nt.items():
            setattr(self, k, v)

    @classmethod
    def getUnique(cls, db, sql, args=None):
        with db.cursor() as cur:
            cur.execute(sql, args)
            assert (cur.rowcount == 1) # If we get multiple, postgresql primary key indexing failed
            return cls(cur.fetchone(), db)

    @classmethod
    def getAll(cls, db, sql, args=None):
        with db.cursor() as cur:
            cur.execute(sql, args)
            return [cls(x, db) for x in cur.fetchall()]

    @classmethod
    def getActive(cls, db):
        return cls.getAll(db, "SELECT * FROM mergeservers WHERE active=true")

    @classmethod
    def getNow(cls, db):
        return cls.getAll(db, "SELECT * FROM mergeservers WHERE mergenow=true")

    @classmethod
    def getLocal(cls, db):
        return cls.getUnique(db, "SELECT * FROM mergeservers WHERE hosttype='localhost'")

    def logSeriesError(self, series, error):
        if "password authentication failed" in error: 
            self.mergestate[series]['error'] = "Password Incorrect"
        else:
            self.mergestate[series]['error'] = error
        self._updateMergeState()
    
    def logMerge(self):
        with self.db.cursor() as localcur:
            self.lastcheck = datetime.datetime.utcnow()
            self.mergenow = False
            localcur.execute("UPDATE mergeservers SET lastcheck=%s, mergenow=%s, mergestate=%s WHERE serverid=%s", (self.lastcheck, self.mergenow, json.dumps(self.mergestate), self.serverid))
            self.db.commit()

    def updateSeriesFrom(self, scandb):
        """ Update the mergestate dict related to deleted or added series """
        with scandb.cursor() as cur:
            cur.execute("SELECT schema_name FROM information_schema.schemata")
            serieslist   = set([x[0] for x in cur.fetchall() if not x[0].startswith('pg_') and x[0] not in ('information_schema', 'public')])
            cachedseries = set(self.mergestate.keys())
            if serieslist == cachedseries:
                return

        for deleted in cachedseries - serieslist:
            del self.mergestate[deleted]
        for added in serieslist - cachedseries:
            self.mergestate[added] = {'latest':0, 'totalhash':'', 'hashes':{}}
        self._updateMergeState()

    def updateCacheFrom(self, scandb, series):
        """ Do any necessary updating of hash data """
        tables = {}
        seriesstate = self.mergestate[series]

        with scandb.cursor() as cur:
            # Do a sanity check on the log tables to see if anyting actually changed since our last check
            cur.execute("SET search_path=%s,%s", (series, 'public'))
            cur.execute("SELECT MAX(times.max) FROM (SELECT max(time) FROM serieslog UNION SELECT max(time) FROM publiclog) AS times")
            result = cur.fetchone()[0]
            if result is None: # brand new database without any data to speak of
                lastlogtime = 1 # initial timestamp is 0, force a blank cache creation
            else:
                lastlogtime = result.timestamp()
            log.debug("lastlog {} - latest at {} = {}".format(lastlogtime, seriesstate['latest'], lastlogtime-seriesstate['latest']))

            # If there is no need to recalculate hashes or update local cache, skip out now
            if lastlogtime <= seriesstate['latest']:
                return 

            # Something has changed, run through the process of caclulating hashes of the PK,modtime combos for each table and combining them together
            for table, command in HASH_COMMANDS.items():
                cur.execute(command)
                assert cur.rowcount == 1, "Invalid return value for hash request"
                tablehash = hashlib.sha1()
                row = cur.fetchone()
                if row[0] is None:
                    tables[table] = b''
                else:
                    for dec in row:
                        tablehash.update(struct.pack('d', dec))
                    tables[table] = tablehash.digest()

            # Convert table hashes to strings
            for name in tables:
                seriesstate['hashes'][name] = base64.b64encode(tables[name]).decode('utf-8')

            # Make note of all blank tables, we can optimize to a download only during merge
            if all(v == b'' for v in tables.values()):
                seriesstate['totalhash'] = ""
            else:
                totalhash = hashlib.sha1()
                for tablehash in tables.values():
                    totalhash.update(tablehash)
                seriesstate['totalhash'] = base64.b64encode(totalhash.digest()).decode('utf-8')
            seriesstate['latest'] = lastlogtime

        self._updateMergeState()


    def _updateMergeState(self):
        # Record changes in the mergeservers table
        with self.db.cursor() as localcur:
            localcur.execute("UPDATE mergeservers SET mergestate=%s WHERE serverid=%s", (json.dumps(self.mergestate), self.serverid))
            self.db.commit()

