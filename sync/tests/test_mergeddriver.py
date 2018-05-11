#!/usr/bin/env python3

import json
import time
import psycopg2
import pytest
import uuid

from helpers import *

def test_mergeddriver(syncdbs, syncdata):
    """ 'Merged' driver got reinserted, test that case here """
    syncx, mergex = syncdbs
    testdid = uuid.UUID("000000000-000-0000-0000-000000000142")
    testcid = uuid.UUID("000000000-000-0000-0000-000000000143")

    # Insert a driver and car, try and move car without updating mod time
    with syncx['A'].cursor() as cur:
        cur.execute("INSERT INTO drivers (driverid, firstname, lastname, email, username) VALUES (%s, 'first', 'last', 'email', 'other')", (testdid,))
        cur.execute("INSERT INTO cars (carid, driverid, classcode, indexcode, number, useclsmult, attr, modified) VALUES (%s, %s, 'c1', 'i1', 2, 'f', '{}', now())", (testcid, testdid))
        with pytest.raises(psycopg2.InternalError):
            cur.execute("UPDATE cars SET driverid=%s WHERE driverid=%s", (syncdata.driverid, testdid,))

