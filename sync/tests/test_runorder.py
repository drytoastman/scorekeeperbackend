#!/usr/bin/env python3

import datetime
import json
import logging
import pytest
import time

from helpers import *

log = logging.getLogger(__name__)

@pytest.mark.skip
def test_rungroupreorder(syncdbs, syncdata):
    """ Dealing with the advanced merge on the driver table """
    syncx, mergex = syncdbs

    insert = "INSERT INTO runorder (carid, eventid, course, rungroup, row) VALUES (%s, %s, %s, %s, %s)"
    update = "UPDATE runorder SET carid=%s,modified=now() WHERE eventid=%s and course=%s and rungroup=%s and row=%s"

    # Add a second run order row and sync
    with syncx['A'].cursor() as cur:
        cur.execute(insert, (syncdata.carid2, syncdata.eventid, 1, 1, 2))
        syncx['A'].commit()

    time.sleep(0.1)
    dosync(syncx['A'], mergex['A'])

    # Simulate a runorder reorder
    with syncx['A'].cursor() as cur:
        cur.execute(update, (syncdata.carid2, syncdata.eventid, 1, 1, 1))
        cur.execute(update, (syncdata.carid,  syncdata.eventid, 1, 1, 2))
        syncx['A'].commit()
    time.sleep(0.1)

    # Different reorder on B
    with syncx['B'].cursor() as cur:
        cur.execute(update, (syncdata.carid3, syncdata.eventid, 1, 1, 1))
        cur.execute(update, (syncdata.carid2, syncdata.eventid, 1, 1, 2))
        cur.execute(insert, (syncdata.carid,  syncdata.eventid, 1, 1, 3))
        syncx['B'].commit()

    time.sleep(0.1)
    dosync(syncx['A'], mergex['A'])

    verify_runorder(syncx, (syncdata.eventid, 1, 1, 1), (('carid', syncdata.carid3),))
    verify_runorder(syncx, (syncdata.eventid, 1, 1, 2), (('carid', syncdata.carid2),))
    verify_runorder(syncx, (syncdata.eventid, 1, 1, 3), (('carid', syncdata.carid1),))
