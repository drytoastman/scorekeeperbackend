
from collections import OrderedDict
import datetime
import hashlib
import json
import logging
import psycopg2
import psycopg2.extras
import struct
psycopg2.extras.register_uuid()

# publiclog, serieslog and mergeservers are used during merging but are never merged themselves
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

log  = logging.getLogger(__name__)
SUMPART = "sum(('x' || substring(t.rowhash, {}, 8))::bit(32)::bigint)"
SUMS = "{}, {}, {}, {}".format(SUMPART.format(1), SUMPART.format(9), SUMPART.format(17), SUMPART.format(25))
LOCALTIME = datetime.datetime(9999, 1, 1)

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

def setSeries(db, series):
    with db.cursor() as cur:
        cur.execute("set search_path=%s,%s", (series, 'public'))

def loadHashes(db):
    ret = {}
    with db.cursor() as cur:
        for table, pk in TABLES.items():
            md5cols = '||'.join("md5({}::text)".format(k) for k in pk+['modified'])
            cur.execute("SELECT {} FROM (SELECT MD5({}) as rowhash from {}) as t".format(SUMS, md5cols, table))
            if cur.rowcount != 1:
                raise Exception('Invalid return value for hash request')
            tablehash = hashlib.sha1()
            row = cur.fetchone()
            if row[0] is None:
                ret[table] = b''
            else:
                for dec in row:
                    tablehash.update(struct.pack('d', dec))
                ret[table] = tablehash.digest()

    finalhash = hashlib.sha1()
    for tablehash in ret.values():
        finalhash.update(tablehash)
    ret['all'] = finalhash.digest()
    for name in ret:
        ret[name] = base64.b64encode(ret[name]).decode('utf-8')
    return ret

def loadPk(db, table):
    if table not in TABLES:
        return {"error":"No such table " + table}
    with db.cursor() as cur:
        cur.execute("SELECT {} from {}".format(','.join(TABLES[table]+['modified']), table))
        return cur.fetchall()

def getSeriesList(db):
    ret = list()
    with db.cursor() as cur:
        cur.execute("SELECT schema_name FROM information_schema.schemata")
        return [x[0] for x in cur.fetchall() if not x[0].startswith('pg_') and x[0] not in ('information_schema', 'public')]
    return ret
 
# For storage of server information 

def updateServerState(db, serverid, **kwargs):
    with db.cursor() as cur:
        cur.execute("SELECT mergestate FROM mergeservers WHERE serverid=%s", (serverid,))
        mergestate = cur.fetchone()[0]
        for k, v in kwargs.items():
            mergestate[k] = v
        cur.execute("UPDATE mergeservers SET mergestate=%s WHERE serverid=%s", (json.dumps(mergestate), serverid))
        db.commit()

def getLocalServerId(db):
    with db.cursor() as cur:
        cur.execute("SELECT serverid FROM mergeservers WHERE address='localhost' and discovered='epoch'")
        if cur.rowcount != 1:
            log.error("Invalid number of localhost entries in mergeservers ({})".format(cur.rowcount))
        return cur.fetchone()[0]

def getActiveServerIds(db):
    with db.cursor() as cur:
        cur.execute("SELECT serverid FROM mergeservers WHERE discovered>='2000-01-01'", ())
        return [x[0] for x in cur.fetchall()] 

def getServerInfo(db, serverid):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM mergeservers WHERE serverid=%s", (serverid,))
        return cur.fetchone()

