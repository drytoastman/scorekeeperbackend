#!/usr/bin/env python3

import collections
import logging
import os
import psycopg2
import psycopg2.extras
import pytest
import subprocess
import sys
import time
import types
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))

from synclogic.process import MergeProcess
from synclogic.model import DataInterface

DB = collections.namedtuple('DB', ['name', 'port', 'serverid'])
DBIMAGE = 'drytoastman/scdb:' + (os.environ.get('TRAVIS_TAG', '') or 'latest')

log = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def syncdata():
    dbs = (DB('A', '7432',  uuid.uuid1()),
           DB('B', '8432',  uuid.uuid1()),
           DB('C', '9432',  uuid.uuid1()),
           DB('D', '10432', uuid.uuid1()))

    yield types.SimpleNamespace(
        driverid = uuid.UUID('00000000-0000-0000-0000-000000000001'),
        carid    = uuid.UUID('00000000-0000-0000-0000-000000000002'),
        carid2   = uuid.UUID('00000000-0000-0000-0000-000000000003'),
        carid3   = uuid.UUID('00000000-0000-0000-0000-000000000004'),
        eventid  = uuid.UUID('00000000-0000-0000-0000-000000000010'),
        series   = 'testseries',
        dbinfo   = dbs)

    subprocess.run("docker kill `docker ps -q -a --filter label=pytest`", shell=True)


@pytest.fixture(scope="module")
def sync1db(request, syncdata):
    return _createdbs(request, syncdata, 1)

@pytest.fixture(scope="module")
def syncdbs(request, syncdata):
    return _createdbs(request, syncdata, 2)

@pytest.fixture(scope="module")
def sync4dbs(request, syncdata):
    return _createdbs(request, syncdata, 4)


@pytest.fixture(scope="module")
def dataentry(request, syncdata):
    de = psycopg2.connect(host='127.0.0.1', user='localuser', dbname='scorekeeper', port=7432, application_name='dataentry')
    with de.cursor() as cur:
        cur.execute("SET search_path=%s,'public'", (syncdata.series, ))
    return de


def _createdbs(request, syncdata, count):
    cargs = { 'host':"127.0.0.1", 'user':'postgres', 'dbname':'scorekeeper', 'connect_timeout':20, 'cursor_factory':psycopg2.extras.DictCursor }
    active = syncdata.dbinfo[:count]

    def teardown():
        subprocess.run(["docker", "kill"] + ["sync"+db.name for db in active], stdout=subprocess.DEVNULL)
    request.addfinalizer(teardown)

    for db in active:
        p = subprocess.run(["docker", "run", "-d", "--rm", "--cap-add=NET_ADMIN", "--cap-add=NET_RAW", "-e", "NOCLIENTCERT=1", "--label", "pytest", "--mount", "type=tmpfs,destination=/var/lib/postgresql/data",
                            "--name", "sync"+db.name, "-p", "{}:6432".format(db.port), "-e", "UI_TIME_ZONE=US/Pacific", DBIMAGE], stdout=subprocess.DEVNULL)
        if p.returncode != 0:
            raise Exception("Failed to start " + db.name)

    # Wait until introspection on db0 works
    for ii in range(20):
        try:
            # Introspection needed by MergeProcess
            DataInterface.initialize(port=int(active[0].port))
            break
        except Exception as e:
            #log.warning(e)
            time.sleep(1)
    else:
        raise Exception("Unable to initialize data interface")

    syncx = {}
    mergex = {}
    for db in active:
        for jj in range(20):
            try:
                con = psycopg2.connect(**cargs, port=db.port)
                break
            except Exception as e:
                #log.warning(e)
                time.sleep(1)
        else:
            raise Exception("Unable to get connection to {}".format(db.name))

        with con.cursor() as cur:
            cur.execute("SET search_path=%s,'public'", (syncdata.series, ))
            cur.execute("INSERT INTO mergeservers(serverid, hostname, address, ctimeout) VALUES ('00000000-0000-0000-0000-000000000000', 'localhost', '127.0.0.1', 10)")
            for db2 in active:
                if db2 != db:
                    cur.execute("SELECT verify_user(%s, %s)",  (syncdata.series, syncdata.series))
                    cur.execute("SELECT verify_series(%s)",    (syncdata.series, ))
                    cur.execute("INSERT INTO mergeservers(serverid, hostname, address, ctimeout, hoststate) VALUES (%s, %s, %s, 5, 'A')", (db2.serverid, db2.name, '127.0.0.1:{}'.format(db2.port)))
        con.commit()
        syncx[db.name]  = con
        mergex[db.name] = MergeProcess([db.port])


    # Setup some initial data
    with syncx[active[0].name].cursor() as cur, open(os.path.join(os.path.dirname(__file__), 'testdata/basic.sql'), 'r') as fp:
        for line in fp:
            sql = line.strip()
            if sql:
                cur.execute(sql)
        syncx[active[0].name].commit()

    # Do an initial merge from first db
    mergex[active[0].name].runonce()

    return syncx, mergex
