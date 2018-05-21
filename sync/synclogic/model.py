
import base64
from collections import OrderedDict, namedtuple
import contextlib
import datetime
import hashlib
import json
import logging
import operator
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
    'weekendmembers',
    'timertimes',
    'settings',
    'indexlist',
    'paymentaccounts',
    'paymentitems',
    'events',   
    'classlist',
    'classorder',
    'cars',
    'registered',
    'payments',
    'runorder',
    'runs',
    'challenges',
    'challengerounds',
    'challengeruns',
]

PUBLIC_TABLES = [
    'drivers',
    'weekendmembers'
]

ADVANCED_TABLES = [
    'drivers'
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


def pkfromjson(table, data):
    """
        JSON logs will store UUID as text, use this to turn them back into UUID's when parsing,
        but only if the column was originally UUID.  Otherwise text columns with a UUID like string
        will get converted as well which is incorrect.
    """
    return tuple([ptype=='uuid' and uuid.UUID(data[k]) or data[k] for k,ptype in PRIMARY_KEYS[table].items()])


def logtablefor(table):
    return table in PUBLIC_TABLES and 'publiclog' or 'serieslog'


class DataInterface(object):

    @classmethod
    def initialize(cls, port=-1):
        """ A little introspection to load the schema from database so we don't have to keep a local copy in this file """
        global SCHEMA_VERSION
        with DataInterface.connectLocal(port) as db:
            with db.cursor() as cur:
                cur.execute("SELECT version FROM version")
                SCHEMA_VERSION = cur.fetchone()[0]

                # Need to set a valid series so we can inspect the format
                testseries = ('template', 'public')
                cur.execute("set search_path=%s,%s", testseries)

                # Determing the primary keys for each table
                for table in TABLE_ORDER:
                    cur.execute("SELECT a.attname,t.typname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) JOIN pg_type t ON t.oid=a.atttypid " \
                                "WHERE i.indrelid = '{}'::regclass AND i.indisprimary".format(table))
                    PRIMARY_KEYS[table] = OrderedDict({row[0]:row[1] for row in cur.fetchall()})

                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s and table_schema in %s", (table, testseries))
                    COLUMNS[table] = [row[0] for row in cur.fetchall()]
                    NONPRIMARY[table] = list(set(COLUMNS[table]) - set(PRIMARY_KEYS[table].keys()))

        SUMPART = "sum(('x' || substring(t.rowhash, {}, 8))::bit(32)::bigint)"
        SUMS = "{}, {}, {}, {}".format(SUMPART.format(1), SUMPART.format(9), SUMPART.format(17), SUMPART.format(25))
        for table, pk in PRIMARY_KEYS.items():
            md5cols = '||'.join("md5({}::text)".format(k) for k in list(pk.keys())+['modified'])
            HASH_COMMANDS[table] = "SELECT {} FROM (SELECT MD5({}) as rowhash from {}) as t".format(SUMS, md5cols, table)


    @classmethod
    def connectLocal(cls, port=-1):
        args = {
          "cursor_factory": psycopg2.extras.DictCursor,
                    "host": "/var/run/postgresql",
                    "user": "postgres",  # Needed to load passwords for use on connecting to other servers
                  "dbname": "scorekeeper",
        "application_name": "synclocal"
        }
        if port > 0:
            args.update({"host": "127.0.0.1", "port": port})
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
           # Must add host, user and password
        }
        try:
            if ':' in server.address:  # If address has a port specified, use it
                (address, port) = server.address.split(':')
                args['port'] = port
            else:
                address = server.address or server.hostname
            db = psycopg2.connect(host=address, user=user, password=password, connect_timeout=server.ctimeout, **args)
            with db.cursor() as cur:
                cur.execute("set idle_in_transaction_session_timeout=2000")
            return db
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
        if len(objs) == 0: return True
        stmt = "INSERT INTO {} ({}) VALUES ({})".format(objs[0].table, ",".join(COLUMNS[objs[0].table]), ",".join(["%({})s".format(x) for x in COLUMNS[objs[0].table]]))
        with db.cursor() as cur:
            try:
                cur.execute("SAVEPOINT insert_savepoint")
                psycopg2.extras.execute_batch(cur, stmt, [o.data for o in objs])
            except psycopg2.IntegrityError as e:
                if e.pgcode == '23503':  # Foreign Key constraint, other stuff needs to happen before we do this
                    cur.execute("ROLLBACK TO SAVEPOINT insert_savepoint")
                    return False
                else:
                    raise e
        return True

    @classmethod
    def update(cls, db, objs):
        if len(objs) == 0: return True
        stmt = "UPDATE {} SET {} WHERE {}".format(objs[0].table, ", ".join("{}=%({})s".format(k,k) for k in NONPRIMARY[objs[0].table]), " AND ".join("{}=%({})s".format(k, k) for k in PRIMARY_KEYS[objs[0].table]))
        with db.cursor() as cur:
            try:
                cur.execute("SAVEPOINT update_savepoint")
                psycopg2.extras.execute_batch(cur, stmt, [o.data for o in objs])
            except psycopg2.IntegrityError as e:
                if e.pgcode == '23503':  # Foreign Key constraint, other stuff needs to happen before we do this
                    cur.execute("ROLLBACK TO SAVEPOINT update_savepoint")
                    return False
                else:
                    raise e
        return True


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
        logu = "UPDATE {} SET otime=%s WHERE otime=CURRENT_TIMESTAMP".format(logtablefor(objs[0].table))
        with db.cursor() as cur:
            cur.execute("SAVEPOINT delete_savepoint")
            for obj in objs:
                try:
                    cur.execute(stmt, obj.data)
                    cur.execute(logu, (obj.deletedat,))
                except psycopg2.IntegrityError as e:
                    if e.pgcode == '23503':  # Foreign Key constraint, need to add the data back to the other side and restart the sync
                        log.warning("Constraint error, adding to undelete: {}, {}".format(obj.pk, e))
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


InsertObject = namedtuple('InsertObject', 'otime, data')
UpdateObject = namedtuple('UpdateObject', 'otime, odiff, adiff, adel')


class LoggedObject():
    """ An object loaded from the log data insert and following updates across multiple machines """

    def __init__(self, table, pk):
        self.table   = table
        self.pk      = pk
        self.initA   = None
        self.initB   = None
        self.updates = []

    def insert(self, otime, newdata):
        if 'created' not in newdata:
            # HACK: fix for missing columns
            newdata['created'] = "1970-01-01T00:00:00"
        if not self.initA:
            self.initA = InsertObject(otime, newdata)
            return
        if not self.initB:
            self.initB = InsertObject(otime, newdata)
            return

        raise Exception("inserted thrice?")

    def _diffobj(self, data1, data2):
        attr1 = data1.pop('attr', dict())
        attr2 = data2.pop('attr', dict())
        odiff = dict(set(data2.items()) - set(data1.items()))  # Differences in object columns
        adiff = dict(set(attr2.items()) - set(attr1.items()))  # Additions/Differences in attr
        adel  = attr1.keys() - attr2.keys()                    # Attr keys that were deleted
        return (odiff, adiff, adel)

    def _issame(self, data1, data2):
        (odiff, adiff, adel) = self._diffobj(data1, data2)
        return not odiff and not adiff and not adel

    def update(self, time, olddata, newdata):
        (odiff, adiff, adel) = self._diffobj(olddata, newdata)
        self.updates.append(UpdateObject(time, odiff, adiff, adel))

    def _convert2logformat(self, dbobj):
        # Convert psycopg2 data into something we can compare with JSON logs
        compare = dict()
        for k in dbobj.keys():
            data = dbobj[k]
            if k == 'attr':
                compare['attr'] = data
            elif type(data) is datetime.datetime:
                compare[k] = data.isoformat().strip('0')
            elif type(data) is uuid.UUID:
                compare[k] = str(data)
            else:
                compare[k] = data
        return compare

    def finalize(self, last):
        # Later insert becomes an update to catch any potential changes outside our purview
        if self.initA.otime < self.initB.otime:
            data = self.initA.data.copy()
            self.update(self.initB.otime, self.initA.data, self.initB.data)
        else:
            data = self.initB.data.copy()
            self.update(self.initA.otime, self.initB.data, self.initA.data)

        # And rebuild the object with all of the updates
        for uobj in sorted(self.updates, key=operator.attrgetter('otime')):
            data.update(uobj.odiff)
            data['attr'].update(uobj.adiff)
            for key in uobj.adel:
                data['attr'].pop(key, None)

            # HACK: change old logged membership to barcode, if there hasn't been a barcode change since the schema move
            if 'barcode' not in data:
                data['barcode'] = data['membership']


        # Pick modified time based on object that didn't change or the final modtime + epsilon
        both = False
        if not self._issame(self._convert2logformat(last.data), dict(data.items())):
            both = True
            data['modified'] = (datetime.datetime.strptime(data['modified'], "%Y-%m-%dT%H:%M:%S.%f") + datetime.timedelta(microseconds=1)).isoformat()
        return PresentObject(self.table, self.pk, data), both


    @classmethod
    def loadFrom(cls, objdict, db, pkset, src, table, when):
        with db.cursor() as cur:
            cur.execute("SELECT * FROM {} WHERE tablen=%s and otime>=%s ORDER BY otime".format(src), (table, when))
            for obj in cur.fetchall():

                def tryuuid(txt):
                    try: return uuid.UUID(txt)
                    except: return txt

                if obj['action'] == 'I':
                    pk = pkfromjson(table, obj['newdata'])
                    if pk not in objdict and pk in pkset:
                        objdict[pk] = LoggedObject(table, pk)
                    if pk in objdict:
                        objdict[pk].insert(obj['otime'], obj['newdata'])

                elif obj['action'] == 'U':
                    pk = pkfromjson(table, obj['newdata'])
                    if pk in objdict:
                        objdict[pk].update(obj['otime'], obj['olddata'], obj['newdata'])

                elif obj['action'] == 'D':
                    pk = pkfromjson(table, obj['olddata'])
                    if pk in objdict:
                        raise Exception("LoggedObject delete is invalid")

                else:
                    log.warning("How did we get here?")



class PresentObject():

    def __init__(self, table, pk, data):
        self.table = table
        self.pk = pk
        self.data = data
        self.modified = data['modified']
        self.created = data.get('created', None)

    def __repr__(self):
        return "PresentObject ({}, {}, {})".format(self.table, self.pk, self.data)

    @classmethod
    def minmodtime(cls, d):
        if len(d) == 0:
            return datetime.datetime(2017, 1, 1)
        return min([v.modified for v in d.values()])

    @classmethod
    def mincreatetime(cls, *lists):
        mintime = datetime.datetime(9999, 1, 1)
        for l in lists:
            if len(l):
                mintime = min(mintime, min([v.created for v in l]))
        return mintime

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

        with db.cursor() as cur:
            cur.execute("SELECT otime, olddata FROM {} WHERE action='D' AND tablen=%s AND otime>%s".format(logtablefor(table)), (table, when,))
            for row in cur.fetchall():
                pk = pkfromjson(table, row['olddata'])
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


    def update(self, *args):
        # Record select changes in the mergeservers table
        stmt = "UPDATE mergeservers SET {} WHERE serverid=%(serverid)s".format(", ".join("{}=%({})s".format(k,k) for k in args))
        vals = dict(serverid=self.serverid)
        for k in args:
            if k == 'mergestate':
                vals[k] = json.dumps(self.mergestate)
            else:
                vals[k] = getattr(self, k)

        with self.db.cursor() as localcur:
            localcur.execute(stmt, vals)
            self.db.commit()

    def _ensureSeriesBase(self, series):
        """ Make sure that some required structure is present in a series state object """
        if series not in self.mergestate:
            self.mergestate[series] = {}
        state = self.mergestate[series]

        if 'lastchange' not in state:
            state['lastchange'] = [0,0]
        if 'totalhash' not in state:
            state['totalhash'] = ''
        if 'hashes' not in state:
            state['hashes'] = {}


    def seriesStart(self, series):
        """ Called when we start merging a given series with this remote server """
        self.mergestate[series].pop('error', None)
        self.mergestate[series]['syncing'] = True
        self.update('mergestate')

    def seriesStatus(self, series, status):
        """ Called with current status for the given series while merging with this remote server """
        log.debug("seriesstatus: %s", status)
        self.mergestate[series]['progress'] = status
        self.update('mergestate')

    def seriesDone(self, series, error):
        """ Called when we are done merging the given series with this remote server, error is None for when successful """
        if error is None:
            self.mergestate[series].pop('error', None)
        else:
            log.info("series %s reported %s", series, error)
            if "password authentication failed" in error: 
                self.mergestate[series]['error'] = "Password Incorrect"
            else:
                self.mergestate[series]['error'] = error
        self.mergestate[series].pop('progress', None)
        self.mergestate[series].pop('syncing', None)
        self.update('mergestate')


    def serverStart(self, localseries):
        """ Called when we start a merge process with this remote server """
        for series in localseries:
            if series not in self.mergestate:
                self._ensureSeriesBase(series)
        self.update('mergestate')

    def serverError(self, error):
        """ Called when the merge attempt with the remove server throws an exception, most likely a connection error """
        for series in self.mergestate:
            self.mergestate[series]['error'] = error
        if self.hoststate == '1':
            self.hoststate = 'I'
            self.update('hoststate') # hoststate ownership is shared with frontend
        self.update('mergestate')

    def serverDone(self):
        """ Called when the merge with the remote server completes without any exceptions """
        if self.hoststate == '1':
            self.hoststate = 'I'
            self.update('hoststate') # hoststate ownership is shared with frontend
        self.lastcheck = datetime.datetime.utcnow()
        if self.hoststate in ('A', '1'):
            self.nextcheck = self.lastcheck + datetime.timedelta(seconds=(self.waittime + random.uniform(-5, +5)))
        else:
            self.nextcheck = datetime.datetime.utcfromtimestamp(0)
        self.update('lastcheck', 'nextcheck', 'mergestate') # nextcheck ownership is shared with frontend


    def recordConnectFailure(self):
        self.cfailures += 1
        self.update('cfailures')

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
            self._ensureSeriesBase(added)
        self.update('mergestate')

    def updateCacheFrom(self, scandb, series):
        """ Do any necessary updating of hash data """
        tables = {}
        self._ensureSeriesBase(series)
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
            cur.execute("SELECT MAX(otimes.max) as maxo, MAX(ltimes.max) as maxl FROM " +
                        "(SELECT max(otime) FROM serieslog UNION ALL SELECT max(otime) FROM publiclog) AS otimes, " +
                        "(SELECT max(ltime) FROM serieslog UNION ALL SELECT max(ltime) FROM publiclog) as ltimes")
            result = cur.fetchone()
            # 1 forces initial check on blank database
            lastchange = [result['maxo'] and result['maxo'].timestamp() or 1,
                          result['maxl'] and result['maxl'].timestamp() or 1]

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

        self.update('mergestate')

