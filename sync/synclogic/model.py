
import base64
from collections import OrderedDict
import contextlib
import datetime
import hashlib
import json
import logging
import psycopg2
import psycopg2.extras
#import psycopg2.exten
import struct
psycopg2.extras.register_uuid()
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

log  = logging.getLogger(__name__)

# publiclog, serieslog, mergeservers and mergepasswords are used during merging but are never merged themselves
# results can be generated from tables so there is no need to merge it
# TABLES are OrderedDicts as we need to update tables in a specific order to maintain reference integrity

PUBLIC_TABLES = OrderedDict({
    'drivers':         ['driverid'],
})

SERIES_TABLES =  OrderedDict({
    'timertimes':      ['serverid', 'raw', 'modified'],
    'settings':        ['name'],
    'indexlist':       ['indexcode'],
    'events':          ['eventid'],
    'classlist':       ['classcode'],
    'classorder':      ['eventid', 'classcode', 'rungroup'],
    'cars':            ['carid'],
    'registered':      ['eventid', 'carid'],
    'runorder':        ['eventid', 'course', 'rungroup', 'row'],
    'runs':            ['eventid', 'carid', 'course', 'run'],
    'challenges':      ['challengeid'],
    'challengerounds': ['challengeid', 'round'],
    'challengeruns':   ['challengeid', 'round', 'carid', 'course'],
})

SUMPART = "sum(('x' || substring(t.rowhash, {}, 8))::bit(32)::bigint)"
SUMS = "{}, {}, {}, {}".format(SUMPART.format(1), SUMPART.format(9), SUMPART.format(17), SUMPART.format(25))

PUBLIC_HASH_COMMANDS = OrderedDict()
for table, pk in PUBLIC_TABLES.items():
    md5cols = '||'.join("md5({}::text)".format(k) for k in pk+['modified'])
    PUBLIC_HASH_COMMANDS[table] = "SELECT {} FROM (SELECT MD5({}) as rowhash from {}) as t".format(SUMS, md5cols, table)

SERIES_HASH_COMMANDS = OrderedDict()
for table, pk in SERIES_TABLES.items():
    md5cols = '||'.join("md5({}::text)".format(k) for k in pk+['modified'])
    SERIES_HASH_COMMANDS[table] = "SELECT {} FROM (SELECT MD5({}) as rowhash from {}) as t".format(SUMS, md5cols, table)


LOCALARGS = {
  "cursor_factory": psycopg2.extras.DictCursor,
            "host": "127.0.0.1", #"/var/run/postgresql",
            "port": 6432,
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

def connectLocal():
    return psycopg2.connect(**LOCALARGS)

def connectRemote(host, user, password):
    return psycopg2.connect(host=host, user=user, password=password, **REMOTEARGS)

def copyTable(srcdb, dstdb, series, table):
    log.debug("copy table %s/%s", series, table)
    with srcdb.cursor() as scur, dstdb.cursor() as dcur:
        scur.execute("set search_path=%s,%s", (series, 'public'))
        dcur.execute("set search_path=%s,%s", (series, 'public'))
        scur.execute("select * from {}".format(table))
        values = scur.fetchall()
        psycopg2.extras.execute_values(dcur, "INSERT INTO {} VALUES %s".format(table), values)

def loadPasswords(db):
    ret = dict()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM pg_shadow WHERE passwd NOT LIKE 'md5%'")
        for row in cur.fetchall():
            ret[row['usename']] = row['passwd']
    return ret


@contextlib.contextmanager
def mergelocks(local, localdb, remote, remotedb):
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
        
        cur1.execute("SET session_replication_role='local'")
        cur2.execute("SET session_replication_role='local'")
        cur1.execute("SELECT pg_try_advisory_lock(42)")
        lock1 = cur1.fetchone()[0]
        if lock1:
            cur2.execute("SELECT pg_try_advisory_lock(42)")
            lock2 = cur2.fetchone()[0]
        assert lock1 and lock2, "Unable to obtain both locks, will try again later"
        yield
    finally:
        cur1.execute("SET session_replication_role='origin'")
        cur2.execute("SET session_replication_role='origin'")
        if lock2:
            cur2.execute("SELECT pg_advisory_unlock(42)")
            cur2.close()
        if lock1:
            cur1.execute("SELECT pg_advisory_unlock(42)")
            cur1.close()


class PresentObjects(object):

    def __init__(self):
        self.data = dict()

    def __delitem__(self, key):
        del self.data[key]

    def __getitem__(self, key):
        return self.data[key]

    def keyset(self):
        return set(self.data.keys())

    def minmodtime(self):
        return min(self.data.values())

    @classmethod
    def loadPresent(cls, db, table):
        assert table in SERIES_TABLES, "No such table {}".format(table)
        ret = cls()
        with db.cursor() as cur:
            cur.execute("SELECT {} from {}".format(','.join(SERIES_TABLES[table]+['modified']), table))
            for row in cur.fetchall():
                ret.data[tuple(row[:-1])] = row['modified']
        return ret


# For storage and query of recently deleted objects
class DeletedObjects(object):

    def __init__(self, pk):
        self.compare = list(enumerate(pk))
        self.data = list()
        self.times = list()

    def append(self, obj, deletetime):
        self.data.append(obj)
        self.times.append(deletetime)

    def contains(self, key):
        """ returns true if the given primary key data is found in the deleted list """
        for obj in self.data:
            for ii, k in self.compare:
                if str(obj[k]) == str(key[ii]):
                    return True
        return False

    @classmethod
    def deletedSince(cls, db, table, when):
        assert table in SERIES_TABLES, "No such table {}".format(table)
        ret = cls(SERIES_TABLES[table])
        with db.cursor() as cur:
            cur.execute("select time, olddata from serieslog where action='D' and time > %s", (when,))
            for row in cur.fetchall():
                ret.append(row['olddata'], row['time'])
        return ret


# For storage of server information 
class MergeServer(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def getUnique(cls, db, sql, args=None):
        with db.cursor() as cur:
            cur.execute(sql, args)
            assert (cur.rowcount == 1) # If we get multiple, postgresql primary key indexing failed
            return cls(db=db, **cur.fetchone())

    @classmethod
    def getAll(cls, db, sql, args=None):
        with db.cursor() as cur:
            cur.execute(sql, args)
            return [cls(db=db, **x) for x in cur.fetchall()]

    @classmethod
    def getActive(cls, db):
        return cls.getAll(db, "SELECT * FROM mergeservers WHERE active=true")

    @classmethod
    def getNow(cls, db):
        return cls.getAll(db, "SELECT * FROM mergeservers WHERE mergenow=true")

    #@classmethod
    #def getById(cls, db, serverid):
    #    return cls.getUnique(db, "SELECT * FROM mergeservers WHERE serverid=%s", (serverid,))

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
            serieslist   = set([x[0] for x in cur.fetchall() if not x[0].startswith('pg_') and x[0] not in ('information_schema')])
            cachedseries = set(self.mergestate.keys())
            if serieslist == cachedseries:
                return

        for deleted in cachedseries - serieslist:
            del self.mergestate[deleted]
        for added in serieslist - cachedseries:
            self.mergestate[added] = {'calculated':0, 'totalhash':'', 'hashes':{}}
        self._updateMergeState()

    def updateCacheFrom(self, scandb, series):
        log.debug("updateCacheFrom %s - %s", scandb.dsn, series)
        if series != 'public':
            with scandb.cursor() as cur:
                cur.execute("set search_path=%s,%s", (series, 'public'))
            self._updateCacheInternal(scandb, "serieslog", SERIES_HASH_COMMANDS, self.mergestate[series])
        else:
            self._updateCacheInternal(scandb, "publiclog", PUBLIC_HASH_COMMANDS, self.mergestate['public'])
        self._updateMergeState()

    def _updateCacheInternal(self, scandb, logtable, hashcommands, seriesstate):
        """ Do any necessary updating of hash data """
        with scandb.cursor() as cur:
            now = datetime.datetime.utcnow() # Capture early time so we don't miss any changes happening during
            tables = {}

            # Do a sanity check on the log tables to see if anyting actually changed since our last check
            cur.execute("SELECT max(time) FROM {}".format(logtable))
            result = cur.fetchone()[0]
            if result is None: # brand new database without any data to speak of
                lastlogtime = 1 # initial timestamp is 0, force a blank cache creation
            else:
                lastlogtime = result.timestamp()
            log.debug("lastlog {} - calculated at {} = {}".format(lastlogtime, seriesstate['calculated'], lastlogtime-seriesstate['calculated']))

            # If there is no need to recalculate hashes or update local cache, skip out now
            if lastlogtime <= seriesstate['calculated']:
                return 

            # Something has changed, run through the process of caclulating hashes of the PK,modtime combos for each table and combining them together
            for table, command in hashcommands.items():
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
            seriesstate['calculated'] = now.timestamp()

    def _updateMergeState(self):
        # Record changes in the mergeservers table
        with self.db.cursor() as localcur:
            localcur.execute("UPDATE mergeservers SET mergestate=%s WHERE serverid=%s", (json.dumps(self.mergestate), self.serverid))
            self.db.commit()

