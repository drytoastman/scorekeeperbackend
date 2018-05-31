import base64
import datetime
import hashlib
import json
import logging
import random
import struct

from synclogic.exceptions import *
from synclogic.model import DataInterface

log  = logging.getLogger(__name__)

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
    def getQuickRuns(cls, db):
        return cls.getAll(db, "SELECT * FROM mergeservers WHERE hoststate IN ('A') AND quickruns IS NOT NULL and serverid!='00000000-0000-0000-0000-000000000000'")

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


    def runsStart(self, series):
        self.seriesStart(series)

    def runsDone(self, series, error):
        self.seriesDone(series, error)
        self.quickruns = None
        self.update('quickruns')

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
            if ver != DataInterface.SCHEMA_VERSION:
                raise DifferentSchemaException("Different schema {} != {}".format(ver, DataInterface.SCHEMA_VERSION))

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
            for table, command in DataInterface.HASH_COMMANDS.items():
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

