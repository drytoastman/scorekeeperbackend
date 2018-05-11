#!/usr/bin/env python3

import time

from helpers import *

def test_keyinsert(syncdbs, syncdata):
    """ Merge drivers, delete on one while linking to a car on the other, should undelete driver and maintain car """
    syncx, mergex = syncdbs
    testid  = '00000000-0000-0000-0000-000000000042'
    testcid = '00000000-0000-0000-0000-000000000043'

    # Insert remote
    with syncx['B'].cursor() as cur:
        cur.execute("INSERT INTO drivers (driverid, firstname, lastname, email, username) VALUES (%s, 'first', 'last', 'email', 'other')", (testid,))
        syncx['B'].commit()
    time.sleep(0.5)

    dosync(syncx['A'], mergex['A'])
    verify_driver(syncx, testid, (('firstname', 'first'), ('lastname', 'last'), ('email', 'email')), ())

    with syncx['A'].cursor() as cur:
        cur.execute("DELETE FROM drivers WHERE driverid=%s", (testid,))
        syncx['A'].commit()
    time.sleep(0.5)
    with syncx['B'].cursor() as cur:
        cur.execute("INSERT INTO cars (carid, driverid, classcode, indexcode, number, useclsmult, attr, modified) VALUES (%s, %s, 'c1', 'i1', 2, 'f', '{}', now())", (testcid, testid))
        syncx['B'].commit()
    time.sleep(0.5)

    dosync(syncx['A'], mergex['A'])
    verify_driver(syncx, testid, (('firstname', 'first'), ('lastname', 'last'), ('email', 'email')), ())
    verify_car(syncx, testcid, (('classcode', 'c1'),), ())


def test_keyupdate(syncdbs, syncdata):
    """ Test for updating a key column that references another deleted row """
    syncx, mergex = syncdbs
    testid  = '00000000-0000-0000-0000-000000000142'

    with syncx['B'].cursor() as cur:
        cur.execute("INSERT INTO indexlist (indexcode, descrip, value) VALUES ('i2', '', 0.999)")
        cur.execute("INSERT INTO cars (carid, driverid, classcode, indexcode, number, useclsmult, attr, modified) VALUES (%s, %s, 'c1', 'i1', 2, 'f', '{}', now())", (testid, syncdata.driverid))
        syncx['B'].commit()
    time.sleep(0.5)

    dosync(syncx['A'], mergex['A'])
    verify_car(syncx, testid, (('classcode', 'c1'),), ())

    with syncx['A'].cursor() as cur:
        cur.execute("DELETE FROM indexlist WHERE indexcode='i2'")
        syncx['A'].commit()
    with syncx['B'].cursor() as cur:
        cur.execute("UPDATE cars SET indexcode='i2',modified=now() WHERE carid=%s", (testid,))
        syncx['B'].commit()
    time.sleep(0.5)

    dosync(syncx['A'], mergex['A'])
    verify_car(syncx, testid, (('classcode', 'c1'), ('indexcode', 'i2')), ())
    verify_index(syncx, 'i2', (('value', 0.999),))

