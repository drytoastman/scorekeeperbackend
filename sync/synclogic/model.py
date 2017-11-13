
import base64
from collections import OrderedDict
import contextlib
import datetime
import hashlib
import json
import logging
import psycopg2
import psycopg2.extras
import random
import struct
import time
import uuid
psycopg2.extras.register_uuid()
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

log  = logging.getLogger(__name__)

# publiclog, serieslog and mergeservers are used during merging but are never merged themselves
# results can be generated from tables so there is no need to merge it

TABLE_ORDER = [
    'drivers',
    'timertimes',
    'settings',
    'indexlist',
    'paymentaccounts',
    'events',   
    'classlist',
    'classorder',
    'cars',
    'payments',
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
SCHEMA_VERSION = ""

class SyncException(Exception):
    pass

class NoDatabaseException(SyncException):
    pass

class NoLocalHostServer(SyncException):
    pass

class DifferentSchemaException(SyncException):
    pass


class DataInterface(object):

    @classmethod
    def initialize(cls, uselocalhost=False):
        """ A little introspection to load the schema from database so we don't have to keep a local copy in this file """
        global SCHEMA_VERSION
        with DataInterface.connectLocal(uselocalhost) as db:
            with db.cursor() as cur:
                cur.execute("SELECT version FROM version")
                SCHEMA_VERSION = cur.fetchone()[0]

                # Need to set a valid series so we can inspect the format
                testseries = ('template', 'public')
                cur.execute("set search_path=%s,%s", testseries)

                # Determing the primary keys for each table
                for table in TABLE_ORDER:
                    cur.execute("SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)" \
                                "WHERE i.indrelid = '{}'::regclass AND i.indisprimary".format(table))
                    PRIMARY_KEYS[table] = [row[0] for row in cur.fetchall()]

                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s and table_schema in %s", (table, testseries))
                    COLUMNS[table] = [row[0] for row in cur.fetchall()]
                    NONPRIMARY[table] = list(set(COLUMNS[table]) - set(PRIMARY_KEYS[table]))

        SUMPART = "sum(('x' || substring(t.rowhash, {}, 8))::bit(32)::bigint)"
        SUMS = "{}, {}, {}, {}".format(SUMPART.format(1), SUMPART.format(9), SUMPART.format(17), SUMPART.format(25))
        for table, pk in PRIMARY_KEYS.items():
            md5cols = '||'.join("md5({}::text)".format(k) for k in pk+['modified'])
            HASH_COMMANDS[table] = "SELECT {} FROM (SELECT MD5({}) as rowhash from {}) as t".format(SUMS, md5cols, table)

    @classmethod
    def connectLocal(cls, uselocalhost=False):
        args = {
          "cursor_factory": psycopg2.extras.DictCursor,
                    "host": "/var/run/postgresql",
                    "user": "postgres",  # Needed to load passwords for use on connecting to other servers
                  "dbname": "scorekeeper",
        "application_name": "synclocal"
        }
        if uselocalhost:
            args.update({"host": "127.0.0.1", "port": 6432})
        try:
            return psycopg2.connect(**args)
        except Exception as e:
            raise NoDatabaseException(e)

    @classmethod
    def connectRemote(cls, server, user, password):
        args = {
          "cursor_factory": psycopg2.extras.DictCursor,
                    "port": 54329,
                  "dbname": "scorekeeper",
        "application_name": "syncremote",
           # Must addhost, user and password
        }
        try:
            address = server.address or server.hostname
            return psycopg2.connect(host=address, user=user, password=password, connect_timeout=server.ctimeout, **args)
        except:
            server.recordConnectFailure()
            raise

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
            psycopg2.extras.execute_batch(cur, stmt, [o.data for o in objs])

    @classmethod
    def update(cls, db, objs):
        if len(objs) == 0: return
        stmt = "UPDATE {} SET {} WHERE {}".format(objs[0].table, ", ".join("{}=%({})s".format(k,k) for k in NONPRIMARY[objs[0].table]), " AND ".join("{}=%({})s".format(k, k) for k in PRIMARY_KEYS[objs[0].table]))
        with db.cursor() as cur:
            psycopg2.extras.execute_batch(cur, stmt, [o.data for o in objs])

    @classmethod
    def delete(cls, db, objs):
        """
            Delete as well as fix up log as delete trigger has no timestamp to reference and therefore defaults to CURRENT_TIMESTAMP 
            which is correct in the local access case but wrong in the merge case
        """
        undelete = list()
        if len(objs) == 0: 
            return undelete
        stmt = "DELETE FROM {} WHERE {}".format(objs[0].table, " AND ".join("{}=%({})s".format(k,k) for k in PRIMARY_KEYS[objs[0].table]))
        logu = "UPDATE {} SET otime=%s WHERE otime=CURRENT_TIMESTAMP".format((objs[0].table=='drivers') and 'publiclog' or 'serieslog')
        with db.cursor() as cur:
            cur.execute("SAVEPOINT delete_savepoint")
            for obj in objs:
                try:
                    cur.execute(stmt, obj.data)
                    cur.execute(logu, (obj.deletedat,))
                except psycopg2.IntegrityError as e:
                    if e.pgcode == '23503':  # Foreign Key constraint, need to add the data back to the other side and restart the sync
                        undelete.append(obj)
                        cur.execute("ROLLBACK TO SAVEPOINT delete_savepoint")
                    else:
                        raise e
        return undelete 


    @classmethod
    @contextlib.contextmanager
    def mergelocks(cls, local, localdb, remote, remotedb, series):
        """
            Context manager to acquire/release advisory locks on both servers.
            It will throw assertion error if it can't get both.  The logic for
            first lock to obtain is there to help dynamic merging systems in
            obtaining locks in the same order to reduce distributed lock race
            conditions.  The current order is lower serverid first.
            Also sets the series schema path so its all nicely tied away here.
        """
        lock1 = False
        lock2 = False
        tries = 10
        try:
            if local.serverid < remote.serverid:
                cur1 = localdb.cursor()
                cur2 = remotedb.cursor()
            else:
                cur1 = remotedb.cursor()
                cur2 = localdb.cursor()

            cur1.execute("SET search_path=%s,%s", (series, 'public'))
            cur2.execute("SET search_path=%s,%s", (series, 'public'))
            
            while tries > 0:
                cur1.execute("SELECT pg_try_advisory_lock(42)")
                lock1 = cur1.fetchone()[0]
                if lock1:
                    cur2.execute("SELECT pg_try_advisory_lock(42)")
                    lock2 = cur2.fetchone()[0]
                    if lock2:
                        log.debug("Acquired both locks")
                        yield
                        break

                # Failed on lock1 or lock2, release the lock we did get, wait and retry
                log.debug("Unable to obtain locks, sleeping and trying again")
                if lock1: cur1.execute("SELECT pg_advisory_unlock(42)") 
                time.sleep(0.5)
                tries -= 1
            else:
                raise SyncException("Unable to obtain locks, will try again later")

        finally:
            # In case we get thrown here by exception, rollback.  We commit successful work before this happens
            remotedb.rollback()
            localdb.rollback()
            log.debug("Releasing locks (%s, %s)", lock1, lock2)
            # Release locks in opposite order from obtaining to avoid deadlock
            if lock2: cur2.execute("SELECT pg_advisory_unlock(42)")
            if lock1: cur1.execute("SELECT pg_advisory_unlock(42)")
            cur2.close()
            cur1.close()


class PresentObject():

    def __init__(self, table, pk, data):
        self.table = table
        self.pk = pk
        self.data = data
        self.modified = data['modified']

    def __repr__(self):
        return "PresentObject ({}, {}, {})".format(self.table, self.pk, self.data)

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
            cur.execute("SELECT otime, olddata FROM {} WHERE action='D' AND tablen=%s AND otime>%s".format(log), (table, when,))
            for row in cur.fetchall():
                pk = tuple([lift_value(row['olddata'][k]) for k in PRIMARY_KEYS[table]])
                ret[pk] = cls(table, pk, row['olddata'], row['otime'])
        return ret


# For storage of server information 
class MergeServer(object):

    def __init__(self, nt, db):
        self.db = db
        for k,v in nt.items():
            setattr(self, k, v)

    def __repr__(self):
        return "{} ({}/{})".format(self.serverid, self.hostname, self.address)

    @classmethod
    def getAll(cls, db, sql, args=None):
        with db.cursor() as cur:
            cur.execute(sql, args)
            return [cls(x, db) for x in cur.fetchall()]

    @classmethod
    def getActive(cls, db):
        return cls.getAll(db, "SELECT * FROM mergeservers WHERE hoststate IN ('A', '1') and serverid!='00000000-0000-0000-0000-000000000000'")

    @classmethod
    def getLocal(cls, db):
        with db.cursor() as cur:
            cur.execute("SELECT * FROM mergeservers WHERE serverid='00000000-0000-0000-0000-000000000000'")
            if cur.rowcount == 0:
                raise NoLocalHostServer()
            elif cur.rowcount > 1:
                log.warning("Multiple localhost entries in the database")
            return cls(cur.fetchone(), db)

    def seriesStart(self, series):
        self.mergestate[series].pop('error', None)
        self.mergestate[series]['syncing'] = True
        self._updateMergeState()

    def seriesDone(self, series, error):
        if error is None:
            self.mergestate[series].pop('error', None)
        else:
            log.info("series %s reported %s", series, error)
            if "password authentication failed" in error: 
                self.mergestate[series]['error'] = "Password Incorrect"
            else:
                self.mergestate[series]['error'] = error
        self.mergestate[series].pop('syncing', None)
        self._updateMergeState()

    def serverError(self, error):
        for series in self.mergestate:
            self.mergestate[series]['error'] = error
            self._updateMergeState()
    
    def mergeDone(self):
        with self.db.cursor() as localcur:
            if self.hoststate == '1':
                self.hoststate = 'I'
            self.lastcheck = datetime.datetime.utcnow()
            if self.hoststate in ('A', '1'):
                self.nextcheck = self.lastcheck + datetime.timedelta(seconds=(self.waittime + random.uniform(-5, +5)))
            else:
                self.nextcheck = datetime.datetime.utcfromtimestamp(0)
            localcur.execute("UPDATE mergeservers SET lastcheck=%s, nextcheck=%s, hoststate=%s, mergestate=%s WHERE serverid=%s",
                                    (self.lastcheck, self.nextcheck, self.hoststate, json.dumps(self.mergestate), self.serverid))
            self.db.commit()

    def recordConnectFailure(self):
        with self.db.cursor() as localcur:
            self.cfailures += 1
            localcur.execute("UPDATE mergeservers SET cfailures=%s WHERE serverid=%s", (self.cfailures, self.serverid))
            self.db.commit()

    def updateSeriesFrom(self, scandb):
        """ Update the mergestate dict related to deleted or added series """
        with scandb.cursor() as cur:
            cur.execute("SELECT schema_name FROM information_schema.schemata")
            serieslist   = set([x[0] for x in cur.fetchall() if not x[0].startswith('pg_') and x[0] not in ('information_schema', 'public', 'template')])
            cachedseries = set(self.mergestate.keys())
            if serieslist == cachedseries:
                return

        for deleted in cachedseries - serieslist:
            del self.mergestate[deleted]
        for added in serieslist - cachedseries:
            self.mergestate[added] = {'lastchange':0, 'totalhash':'', 'hashes':{}}
        self._updateMergeState()

    def updateCacheFrom(self, scandb, series):
        """ Do any necessary updating of hash data """
        tables = {}
        seriesstate = self.mergestate[series]

        with scandb.cursor() as cur:
            cur.execute("SELECT version FROM version")
            if cur.rowcount != 1:
                raise DifferentSchemaException("No remote schema version")
            ver = cur.fetchone()[0]
            if ver != SCHEMA_VERSION:
                raise DifferentSchemaException("Different schema {} != {}".format(ver, SCHEMA_VERSION))

            # Do a sanity check on the log tables to see if anyting actually changed since our last check
            cur.execute("SET search_path=%s,%s", (series, 'public'))
            cur.execute("SELECT MAX(times.max) FROM (SELECT max(ltime) FROM serieslog UNION ALL SELECT max(ltime) FROM publiclog) AS times")
            result = cur.fetchone()[0]
            lastchange = result and result.timestamp() or 1  # 1 forces initial check on blank database

            # If there is no need to recalculate hashes or update local cache, skip out now
            if lastchange == seriesstate['lastchange']:
                log.debug("%s %s lastlog time shortcut", scandb.dsn.split()[0], series)
                return 

            log.debug("%s %s perform hash computations", scandb.dsn.split()[0], series)
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
            if lastchange is not None:
                seriesstate['lastchange'] = lastchange

        self._updateMergeState()

    def _updateMergeState(self):
        # Record changes in the mergeservers table
        with self.db.cursor() as localcur:
            localcur.execute("UPDATE mergeservers SET mergestate=%s WHERE serverid=%s", (json.dumps(self.mergestate), self.serverid))
            self.db.commit()

