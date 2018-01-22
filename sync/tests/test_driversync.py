#!/usr/bin/env python3

import json
import time

from helpers import *

def test_driversync(syncdbs, syncdata):
    (synca, syncb, merge) = syncdbs
    cruft1 = dict(driverid="c2c32a70-f0fa-11e7-9c7f-5e155307955f", firstname="X")
    cruft2 = dict(driverid="c2c32a70-f0fa-11e7-9c7f-5e155307955f", firstname="Y")

    # Modify firstname and address on A
    with synca.cursor() as cur:
        cur.execute("UPDATE drivers SET firstname=%s,attr=%s,modified=now() where driverid=%s", ('newfirst', json.dumps({'address': '123'}), syncdata.driverid,))
        synca.commit()
    time.sleep(0.1)

    # Modify lastname and zip on B, insert some spurious log data that isn't relavant to us
    with syncb.cursor() as cur:
        cur.execute("UPDATE drivers SET lastname=%s,attr=%s,modified=now() where driverid=%s", ('newlast', json.dumps({'zip': '98111'}), syncdata.driverid,))
        cur.execute("INSERT INTO publiclog (usern, app, tablen, action, otime, ltime, olddata, newdata) VALUES ('x', 'y', 'drivers', 'U', now(), now(), %s, %s)", (json.dumps(cruft1), json.dumps(cruft2)))
        time.sleep(0.1)
        cur.execute("INSERT INTO publiclog (usern, app, tablen, action, otime, ltime, olddata, newdata) VALUES ('x', 'y', 'drivers', 'D', now(), now(), %s, '{}')", (json.dumps(cruft2),))
        syncb.commit()
    time.sleep(0.1)

    # Modify email and zip on A
    with synca.cursor() as cur:
        cur.execute("UPDATE drivers SET email=%s,attr=%s,modified=now() where driverid=%s", ('newemail', json.dumps({'address': '123', 'zip': '98222'}), syncdata.driverid,))
    time.sleep(0.1)

    sync(synca, syncb, merge)
    verify_driver(synca, syncb, syncdata.driverid,
        (('firstname', 'newfirst'), ('lastname', 'newlast'), ('email', 'newemail')),
        (('address', '123'), ('zip', '98222')))

    # Remove zip
    with synca.cursor() as cur:
        cur.execute("UPDATE drivers SET attr=%s,modified=now() where driverid=%s", (json.dumps({'address': '123'}), syncdata.driverid,))
    time.sleep(0.1)

    sync(synca, syncb, merge)
    verify_driver(synca, syncb, syncdata.driverid,
        (('firstname', 'newfirst'), ('lastname', 'newlast'), ('email', 'newemail')),
        (('address', '123'), ('zip', None)))

    # Delete driver on remote
    with syncb.cursor() as cur:
        cur.execute("DELETE FROM registered WHERE carid in (SELECT carid FROM cars WHERE driverid=%s)", (syncdata.driverid,))
        cur.execute("DELETE FROM runorder WHERE carid in (SELECT carid FROM cars WHERE driverid=%s)", (syncdata.driverid,))
        cur.execute("DELETE FROM runs WHERE carid in (SELECT carid FROM cars WHERE driverid=%s)", (syncdata.driverid,))
        cur.execute("DELETE FROM cars WHERE driverid=%s", (syncdata.driverid,))
        cur.execute("DELETE FROM drivers WHERE driverid=%s", (syncdata.driverid,))
    time.sleep(0.1)

    sync(synca, syncb, merge)
    verify_driver(synca, syncb, syncdata.driverid, None, None)


def XXXtest_driverwfkey(syncdbs, syncdata):
    """ Merge drivers, delete on one while linking to a car on the other, should undelete driver and maintain car """
    (synca, syncb, merge) = syncdbs
    testid  = '00000000-0000-0000-0000-000000000042'
    testcid = '00000000-0000-0000-0000-000000000043'

    # Insert remote
    with syncb.cursor() as cur:
        cur.execute("INSERT INTO drivers (driverid, firstname, lastname, email, username) VALUES (%s, 'first', 'last', 'email', 'other')", (testid,))
    time.sleep(0.5)

    sync(synca, syncb, merge)
    verify_driver(synca, syncb, testid, (('firstname', 'first'), ('lastname', 'last'), ('email', 'email')), ())

    with synca.cursor() as cur:
        cur.execute("DELETE FROM drivers WHERE driverid=%s", (testid,))
    time.sleep(0.5)
    with syncb.cursor() as cur:
        cur.execute("INSERT INTO cars (carid, driverid, classcode, indexcode, number, useclsmult, attr, modified) VALUES (%s, %s, 'c1', 'i1', 2, 'f', '{}', now())", (testcid, testid))
    time.sleep(0.5)

    sync(synca, syncb, merge)
    verify_driver(synca, syncb, testid, (('firstname', 'first'), ('lastname', 'last'), ('email', 'email')), ())
    verify_car(synca, syncb, testcid, (('classcode', 'c1'),), ())

