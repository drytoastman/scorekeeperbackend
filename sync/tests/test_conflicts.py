#!/usr/bin/env python3

import time

from helpers import *

def test_keyinsert(syncdbs, syncdata):
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


def test_keyupdate(syncdbs, syncdata):
    """ Test for updating a key column that references another deleted row """
    (synca, syncb, merge) = syncdbs
    testid  = '00000000-0000-0000-0000-000000000142'

    with syncb.cursor() as cur:
        cur.execute("INSERT INTO indexlist (indexcode, descrip, value) VALUES ('i2', '', 0.999)")
        cur.execute("INSERT INTO cars (carid, driverid, classcode, indexcode, number, useclsmult, attr, modified) VALUES (%s, %s, 'c1', 'i1', 2, 'f', '{}', now())", (testid, syncdata.driverid))
    time.sleep(0.5)

    sync(synca, syncb, merge)
    verify_car(synca, syncb, testid, (('classcode', 'c1'),), ())

    with synca.cursor() as cur:
        cur.execute("DELETE FROM indexlist WHERE indexcode='i2'")
    with syncb.cursor() as cur:
        cur.execute("UPDATE cars SET indexcode='i2',modified=now() WHERE carid=%s", (testid,))
    time.sleep(0.5)

    sync(synca, syncb, merge)
    verify_car(synca, syncb, testid, (('classcode', 'c1'), ('indexcode', 'i2')), ())
    verify_index(synca, syncb, 'i2', (('value', 0.999),))

