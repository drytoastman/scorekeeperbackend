#!/usr/bin/env python3

import collections
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

DB = collections.namedtuple('DB', ['name', 'image', 'port', 'serverid'])

@pytest.fixture(scope="module")
def syncdata():
    return types.SimpleNamespace(
        driverid = '00000000-0000-0000-0000-000000000001',
        carid    = '00000000-0000-0000-0000-000000000002',
        eventid  = '00000000-0000-0000-0000-000000000010',
        series   = 'testseries')


@pytest.fixture(scope="module")
def sync1db(request, syncdata):
    TESTDBS = (DB('A', 'drytoastman/scdb:latest', '7432', uuid.uuid1()),)
    syncx, mergex = _createdbs(request, syncdata, TESTDBS)
    return syncx['A'], mergex['A']


@pytest.fixture(scope="module")
def syncdbs(request, syncdata):
    TESTDBS = (
        DB('A', 'drytoastman/scdb:latest', '7432', uuid.uuid1()),
        DB('B', 'drytoastman/scdb:latest', '8432', uuid.uuid1())
    )
    return _createdbs(request, syncdata, TESTDBS)


@pytest.fixture(scope="module")
def sync4dbs(request, syncdata):
    TESTDBS = (
        DB('A', 'drytoastman/scdb:latest',  '7432', uuid.uuid1()),
        DB('B', 'drytoastman/scdb:latest',  '8432', uuid.uuid1()),
        DB('C', 'drytoastman/scdb:latest',  '9432', uuid.uuid1()),
        DB('D', 'drytoastman/scdb:latest', '10432', uuid.uuid1())
    )
    return _createdbs(request, syncdata, TESTDBS)


def _createdbs(request, syncdata, TESTDBS):
    cargs = { 'host':"127.0.0.1", 'user':'postgres', 'dbname':'scorekeeper', 'connect_timeout':20, 'cursor_factory':psycopg2.extras.DictCursor }

    def teardown():
        subprocess.run(["docker", "kill"] + ["sync"+db.name for db in TESTDBS], stdout=subprocess.DEVNULL)
    request.addfinalizer(teardown)

    for db in TESTDBS:
        p = subprocess.run(["docker", "run", "-d", "--rm", "--name", "sync"+db.name, "-p", "{}:6432".format(db.port), "-e", "UI_TIME_ZONE=US/Pacific", db.image], stdout=subprocess.DEVNULL)
        if p.returncode != 0:
            raise Exception("Failed to start " + db.name)

    # Wait until introspection on db0 works
    for ii in range(10):
        try:
            # Introspection needed by MergeProcess
            DataInterface.initialize(port=int(TESTDBS[0].port))
            break
        except Exception as e:
            time.sleep(1)
    else:
        raise Exception("Unable to initialize data interface")


    # Do setup and get connections to each
    syncx = {}
    mergex = {}
    for db in TESTDBS:
        for jj in range(10):
            try:
                con = psycopg2.connect(**cargs, port=db.port)
                break
            except:
                time.sleep(1)
        else:
            raise Exception("Unable to get connection to {}".format(db.name))


        with con.cursor() as cur:
            cur.execute("SELECT verify_user(%s, %s)",  (syncdata.series, syncdata.series))
            cur.execute("SELECT verify_series(%s)",    (syncdata.series, ))
            cur.execute("SET search_path=%s,'public'", (syncdata.series, ))
            cur.execute("INSERT INTO mergeservers(serverid, hostname, address, ctimeout) VALUES ('00000000-0000-0000-0000-000000000000', 'localhost', '127.0.0.1', 10)")
            for db2 in TESTDBS:
                if db2 != db:
                    cur.execute("INSERT INTO mergeservers(serverid, hostname, address, ctimeout, hoststate) VALUES (%s, %s, %s, 2, 'A')", (db2.serverid, db2.name, '127.0.0.1:{}'.format(db2.port)))
        con.commit()
        syncx[db.name]  = con
        mergex[db.name] = MergeProcess([db.port])


    # Setup some initial data
    with syncx[TESTDBS[0].name].cursor() as cur, open(os.path.join(os.path.dirname(__file__), 'testdata/basic.sql'), 'r') as fp:
        for line in fp:
            sql = line.strip()
            if sql:
                cur.execute(sql)
        syncx[TESTDBS[0].name].commit()


    # Do an initial merge from first db
    mergex[TESTDBS[0].name].runonce()

    return syncx, mergex

