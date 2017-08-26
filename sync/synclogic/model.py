
import base64
from collections import OrderedDict
import datetime
import hashlib
import json
import logging
import psycopg2
import psycopg2.extras
import struct
psycopg2.extras.register_uuid()

log  = logging.getLogger(__name__)

# publiclog, serieslog, mergeservers and mergepasswords are used during merging but are never merged themselves
# results can be generated from tables so there is no need to merge it
TABLES =  OrderedDict({
    'timertimes':      ['serverid', 'raw', 'modified'],
    'settings':        ['name'],
    'indexlist':       ['indexcode'],
    'drivers':         ['driverid'],
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
HASHCOMMANDS = dict()
for table, pk in TABLES.items():
    md5cols = '||'.join("md5({}::text)".format(k) for k in pk+['modified'])
    HASHCOMMANDS[table] = "SELECT {} FROM (SELECT MD5({}) as rowhash from {}) as t".format(SUMS, md5cols, table)

LOCALARGS = {
  "cursor_factory": psycopg2.extras.DictCursor,
            "host": "127.0.0.1", #"/var/run/postgresql",
            "port": 6432,
            "user": "localuser",
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

def loadPk(db, table):
    if table not in TABLES:
        return {"error":"No such table " + table}
    with db.cursor() as cur:
        cur.execute("SELECT {} from {}".format(','.join(TABLES[table]+['modified']), table))
        return cur.fetchall()

def loadPasswords(db):
    ret = dict()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM mergepasswords")
        for row in cur.fetchall():
            ret[row['series']] = row['password']
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

    @classmethod
    def getById(cls, db, serverid):
        return cls.getUnique(db, "SELECT * FROM mergeservers WHERE serverid=%s", (serverid,))

    @classmethod
    def getLocal(cls, db):
        return cls.getUnique(db, "SELECT * FROM mergeservers WHERE hosttype='localhost'")

    def logMerge(self):
        with self.db.cursor() as localcur:
            self.lastcheck = datetime.datetime.utcnow()
            self.mergenow = False
            localcur.execute("UPDATE mergeservers SET lastcheck=%s, mergenow=%s WHERE serverid=%s", (self.lastcheck, self.mergenow, self.serverid))
            self.db.commit()

    def updateSeriesFrom(self, scandb):
        """ Update the mergestate dict related to deleted or added series """
        with scandb.cursor() as cur:
            cur.execute("SELECT schema_name FROM information_schema.schemata")
            serieslist   = set([x[0] for x in cur.fetchall() if not x[0].startswith('pg_') and x[0] not in ('information_schema', 'public')])
            cachedseries = set(self.mergestate.keys())
            if serieslist == cachedseries:
                return

        with self.db.cursor() as localcur:
            for deleted in cachedseries - serieslist:
                del self.mergestate[deleted]
            for added in serieslist - cachedseries:
                self.mergestate[added] = {'calculated':0}
            localcur.execute("UPDATE mergeservers SET mergestate=%s WHERE serverid=%s", (json.dumps(self.mergestate), self.serverid))
            self.db.commit()


    def updateCacheFrom(self, scandb, series):
        """ Do any necessary updating of hash data """
        with scandb.cursor() as cur:
            seriesstate = self.mergestate[series]
            now = datetime.datetime.utcnow() # Capture early time so we don't miss any changes happening during
            tables = {}

            cur.execute("set search_path=%s,%s", (series, 'public'))
            cur.execute("SELECT MAX(times.max) FROM (SELECT max(time) FROM serieslog UNION SELECT max(time) FROM publiclog) AS times")
            lastlogtime = cur.fetchone()[0].timestamp()
            log.debug("lastlog {} - calculated at {} = {}".format(lastlogtime, seriesstate['calculated'], lastlogtime-seriesstate['calculated']))
            if lastlogtime <= seriesstate['calculated']:
                return # No update needed

            for table, command in HASHCOMMANDS.items():
                cur.execute(command)
                if cur.rowcount != 1:
                    raise Exception('Invalid return value for hash request')
                tablehash = hashlib.sha1()
                row = cur.fetchone()
                if row[0] is None:
                    tables[table] = b''
                else:
                    for dec in row:
                        tablehash.update(struct.pack('d', dec))
                    tables[table] = tablehash.digest()

            finalhash = hashlib.sha1()
            for tablehash in tables.values():
                finalhash.update(tablehash)
            tables['all'] = finalhash.digest()
            for name in tables:
                seriesstate[name] = base64.b64encode(tables[name]).decode('utf-8')
            seriesstate['calculated'] = now.timestamp()

        with self.db.cursor() as localcur:
            localcur.execute("UPDATE mergeservers SET mergestate=%s WHERE serverid=%s", (json.dumps(self.mergestate), self.serverid))
            self.db.commit()

