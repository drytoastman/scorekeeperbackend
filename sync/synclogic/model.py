from collections import OrderedDict
import contextlib
import logging
import os
import psycopg2
import psycopg2.extras
import time

psycopg2.extras.register_uuid()
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

from synclogic.exceptions import *

log  = logging.getLogger(__name__)

# publiclog, serieslog and mergeservers are used during merging but are never merged themselves
# results can be generated from tables so there is no need to merge it


class DataInterface(object):

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
        'cars',
        'registered',
        'payments',
        'runs',
        'challenges',
        'challengerounds',
        'challengestaging',
        'challengeruns',
        'externalresults'
    ]

    INTERTWINED_DATA = [
        'classorder',
        'runorder'
    ]

    ALL_TABLES = TABLE_ORDER + INTERTWINED_DATA

    PUBLIC_TABLES = [
        'drivers',
        'weekendmembers'
    ]

    ADVANCED_UPDATE_TABLES = [
        'drivers'
    ]

    SCHEMA_VERSION = "INIT"

    LOCAL_TIMEOUT  = 5
    PEER_TIMEOUT   = 8
    REMOTE_TIMEOUT = 60
    APP_TIME_LIMIT = 3.0
    WEB_TIME_LIMIT = 5.0

    COLUMNS       = dict()
    PRIMARY_KEYS  = dict()
    NONPRIMARY    = dict()
    HASH_COMMANDS = dict()

    @classmethod
    def logtablefor(cls, table):
        return table in DataInterface.PUBLIC_TABLES and 'publiclog' or 'serieslog'

    @classmethod
    def initialize(cls, port=-1):
        """ A little introspection to load the schema from database so we don't have to keep a local copy in this file """
        with DataInterface.connectLocal(port) as db:
            with db.cursor() as cur:
                cur.execute("SELECT version FROM version")
                DataInterface.SCHEMA_VERSION = cur.fetchone()[0]

                # Need to set a valid series so we can inspect the format
                testseries = ('template', 'public')
                cur.execute("set search_path=%s,%s", testseries)

                # Determing the primary keys for each table
                for table in DataInterface.ALL_TABLES:
                    cur.execute("SELECT a.attname,t.typname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) JOIN pg_type t ON t.oid=a.atttypid " \
                                "WHERE i.indrelid = '{}'::regclass AND i.indisprimary".format(table))
                    DataInterface.PRIMARY_KEYS[table] = OrderedDict({row[0]:row[1] for row in cur.fetchall()})

                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s and table_schema in %s", (table, testseries))
                    DataInterface.COLUMNS[table] = [row[0] for row in cur.fetchall()]
                    DataInterface.NONPRIMARY[table] = list(set(DataInterface.COLUMNS[table]) - set(DataInterface.PRIMARY_KEYS[table].keys()))

        SUMPART = "sum(('x' || substring(t.rowhash, {}, 8))::bit(32)::bigint)"
        SUMS = "{}, {}, {}, {}".format(SUMPART.format(1), SUMPART.format(9), SUMPART.format(17), SUMPART.format(25))
        for table, pk in DataInterface.PRIMARY_KEYS.items():
            md5cols = '||'.join("md5({}::text)".format(k) for k in list(pk.keys())+['modified'])
            DataInterface.HASH_COMMANDS[table] = "SELECT {} FROM (SELECT MD5({}) as rowhash from {}) as t".format(SUMS, md5cols, table)


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
            db = psycopg2.connect(**args)
            with db.cursor() as cur:
                log.debug("Setting LOCAL transaction timeout: %s", DataInterface.LOCAL_TIMEOUT*1000)
                cur.execute("set idle_in_transaction_session_timeout={}".format(DataInterface.LOCAL_TIMEOUT * 1000))
            return db
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

            if args['port'] in (54329, ):
                args.update({
                      "sslkey": "/certs/server.key",
                     "sslcert": "/certs/server.cert",
                 "sslrootcert": "/certs/root.cert",
                     "sslmode": "verify-ca"
                })

            db = psycopg2.connect(host=address, user=user, password=password, connect_timeout=server.ctimeout, **args)
            with db.cursor() as cur:
                if server.address:
                    log.debug("Setting PEER transaction timeout: %s", DataInterface.PEER_TIMEOUT*1000)
                    cur.execute("set idle_in_transaction_session_timeout={}".format(DataInterface.PEER_TIMEOUT*1000))
                else:
                    log.debug("Setting REMOTE transaction timeout: %s", DataInterface.REMOTE_TIMEOUT*1000)
                    cur.execute("set idle_in_transaction_session_timeout={}".format(DataInterface.REMOTE_TIMEOUT*1000))
            return db
        except:
            server.recordConnectFailure()
            raise

    @classmethod
    def loadPasswords(cls, db):
        ret = dict()
        with db.cursor() as cur:
            cur.execute("SELECT * FROM localcache")
            for row in cur.fetchall():
                ret[row['name']] = row['data']
        return ret

    @classmethod
    def insert(cls, db, objs, commit=True):
        if len(objs) == 0: return True
        stmt = "INSERT INTO {} ({}) VALUES ({})".format(objs[0].table, ",".join(DataInterface.COLUMNS[objs[0].table]), ",".join(["%({})s".format(x) for x in DataInterface.COLUMNS[objs[0].table]]))
        with db.cursor() as cur:
            try:
                cur.execute("SAVEPOINT insert_savepoint")
                psycopg2.extras.execute_batch(cur, stmt, [o.data for o in objs])
                if commit:
                    db.commit()
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
        stmt = "UPDATE {} SET {} WHERE {}".format(objs[0].table, ", ".join("{}=%({})s".format(k,k) for k in DataInterface.NONPRIMARY[objs[0].table]), " AND ".join("{}=%({})s".format(k, k) for k in DataInterface.PRIMARY_KEYS[objs[0].table]))
        with db.cursor() as cur:
            try:
                cur.execute("SAVEPOINT update_savepoint")
                psycopg2.extras.execute_batch(cur, stmt, [o.data for o in objs])
                db.commit()
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
        stmt = "DELETE FROM {} WHERE {}".format(objs[0].table, " AND ".join("{}=%({})s".format(k,k) for k in DataInterface.PRIMARY_KEYS[objs[0].table]))
        logu = "UPDATE {} SET otime=%s WHERE otime=CURRENT_TIMESTAMP".format(DataInterface.logtablefor(objs[0].table))
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
        if not undelete:
            db.commit()
        return undelete 


    @classmethod
    def seriesList(cls, db):
        with db.cursor() as cur:
            cur.execute("select schema_name from information_schema.schemata")
            return sorted(s[0] for s in cur.fetchall() if not s[0].startswith('pg_') and s[0] not in ("information_schema", "public", "template"))


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
                time.sleep(1.0)
                tries -= 1
            else:
                raise SyncException("Unable to obtain locks, will try again later")

        finally:
            # In case we get thrown here by exception, rollback.  We commit successful work before this happens
            try: remotedb.rollback()
            except: pass
            try: localdb.rollback()
            except: pass
            log.debug("Releasing locks (%s, %s)", lock1, lock2)
            # Release locks in opposite order from obtaining to avoid deadlock
            if lock2:
                try:
                    cur2.execute("SELECT pg_advisory_unlock(42)")
                    cur2.close()
                except:
                    pass
            if lock1:
                try:
                    cur1.execute("SELECT pg_advisory_unlock(42)")
                    cur1.close()
                except:
                    pass
