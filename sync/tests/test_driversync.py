#!/usr/bin/env python3

import json
import os
import psycopg2
import psycopg2.extras
import pytest
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))

from synclogic.process import MergeProcess
from synclogic.model import DataInterface


@pytest.fixture(scope="session")
def testdbs():
    TESTDBS = (('synca', 'drytoastman/scdb:testdb', '6432:6432'), ('syncb', 'drytoastman/scdb:latest', '7432:6432'))
    cargs = { 'host':"127.0.0.1", 'user':'postgres', 'dbname':'scorekeeper', 'connect_timeout':20, 'cursor_factory':psycopg2.extras.DictCursor }

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
        subprocess.run(["docker", "kill"] + [x[0] for x in TESTDBS], stdout=subprocess.DEVNULL)
        raise Exception("Unable to initialize data interface")


    with synca.cursor() as cur:
        cur.execute("INSERT INTO mergeservers(serverid, hostname, address, ctimeout, hoststate) VALUES ('00000000-0000-0000-1111-000000000000', 'syncb', '127.0.0.1:7432', 2, 'A')")
        synca.commit()

    with syncb.cursor() as cur:
        cur.execute("SELECT verify_user('testseries', 'testseries')")
        cur.execute("SELECT verify_series('testseries')")
        syncb.commit()

    # Do an initial merge
    merge = MergeProcess(["--uselocalhost"])
    merge.runonce()

    yield (synca, syncb, merge)

    subprocess.run(["docker", "kill"] + [x[0] for x in TESTDBS], stdout=subprocess.DEVNULL)



def test_driversync(testdbs):
    driverid = '00000000-0000-0000-0000-000000000001'
    (synca, syncb, merge) = testdbs

    # Modify firstname and address on A
    with synca.cursor() as cur:
        cur.execute("UPDATE drivers SET firstname=%s,attr=%s,modified=now() where driverid=%s", ('newfirst', json.dumps({'address': '123'}), driverid,))
        synca.commit()
    time.sleep(0.1)

    # Modify lastname and zip on B
    with syncb.cursor() as cur:
        cur.execute("UPDATE drivers SET lastname=%s,attr=%s,modified=now() where driverid=%s", ('newlast', json.dumps({'zip': '98111'}), driverid,))
        syncb.commit()
    time.sleep(0.1)

    # Modify email and zip on A
    with synca.cursor() as cur:
        cur.execute("UPDATE drivers SET email=%s,attr=%s,modified=now() where driverid=%s", ('newemail', json.dumps({'address': '123', 'zip': '98222'}), driverid,))
    time.sleep(0.1)

    sync_and_verify_driver(synca, syncb, merge, driverid,
        (('firstname', 'newfirst'), ('lastname', 'newlast'), ('email', 'newemail')),
        (('address', '123'), ('zip', '98222')))

    # Delete zip
    with synca.cursor() as cur:
        cur.execute("UPDATE drivers SET attr=%s,modified=now() where driverid=%s", (json.dumps({'address': '123'}), driverid,))
    time.sleep(0.1)

    sync_and_verify_driver(synca, syncb, merge, driverid,
        (('firstname', 'newfirst'), ('lastname', 'newlast'), ('email', 'newemail')),
        (('address', '123'), ('zip', None)))


def sync_and_verify_driver(synca, syncb, merge, driverid, coltuple, attrtuple):
    # Sync and then load drivers from both sides and verify that they are as intended
    with synca.cursor() as cura, syncb.cursor() as curb:
        cura.execute("UPDATE mergeservers SET lastcheck='epoch', nextcheck='epoch'")
        synca.commit()
        merge.runonce()
        cura.execute("SELECT *  FROM drivers WHERE driverid=%s", (driverid,))
        curb.execute("SELECT *  FROM drivers WHERE driverid=%s", (driverid,))
        da = cura.fetchone()
        db = curb.fetchone()

    for key, expected in coltuple: 
        assert da[key] == expected
    for key, expected in attrtuple: 
        assert da['attr'].get(key, None) == expected

