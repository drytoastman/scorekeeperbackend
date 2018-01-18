#!/usr/bin/env python3

import os
import psycopg2
import psycopg2.extras
import pytest
import subprocess
import sys
import time
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))

from synclogic.process import MergeProcess
from synclogic.model import DataInterface

@pytest.fixture(scope="module")
def syncdata():
    return types.SimpleNamespace(
        driverid = '00000000-0000-0000-0000-000000000001',
        carid    = '00000000-0000-0000-0000-000000000002',
        eventid  = '00000000-0000-0000-0000-000000000010',
        series   = 'testseries')


@pytest.fixture(scope="module")
def syncdbs(request, syncdata):
    TESTDBS = (('synca', 'drytoastman/scdb:testdb', '6432:6432'), ('syncb', 'drytoastman/scdb:latest', '7432:6432'))
    cargs = { 'host':"127.0.0.1", 'user':'postgres', 'dbname':'scorekeeper', 'connect_timeout':20, 'cursor_factory':psycopg2.extras.DictCursor }

    def teardown():
        subprocess.run(["docker", "kill"] + [name for (name, _, _) in TESTDBS], stdout=subprocess.DEVNULL)
    request.addfinalizer(teardown)

    for name, image, port in TESTDBS:
        p = subprocess.run(["docker", "run", "-d", "--rm", "--name", name, "-p", port, image], stdout=subprocess.DEVNULL)
        if p.returncode != 0:
            raise Exception("Failed to start " + name)

    for ii in range(10):
        try:
            # Introspection needed by MergeProcess
            DataInterface.initialize(True)
            synca = psycopg2.connect(**cargs, port=6432)
            syncb = psycopg2.connect(**cargs, port=7432)
            break
        except Exception as e:
            time.sleep(1)
    else:
        raise Exception("Unable to initialize data interface")

    with synca.cursor() as cur:
        cur.execute("INSERT INTO mergeservers(serverid, hostname, address, ctimeout, hoststate) VALUES ('00000000-0000-0000-1111-000000000000', 'syncb', '127.0.0.1:7432', 2, 'A')")
        synca.commit()

    with syncb.cursor() as cur:
        cur.execute("SELECT verify_user(%s, %s)", (syncdata.series, syncdata.series))
        cur.execute("SELECT verify_series(%s)", (syncdata.series, ))
        syncb.commit()

    # Do an initial merge
    merge = MergeProcess(["--uselocalhost"])
    merge.runonce()

    return (synca, syncb, merge)

