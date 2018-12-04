#!/usr/bin/env python3

import datetime
import logging
import psycopg2
import pytest
import time
import uuid

from helpers import *

log = logging.getLogger(__name__)

def test_rungroup_reorder(syncdbs, syncdata):
    syncx, mergex = syncdbs

    insert = "INSERT INTO runorder (cars, eventid, course, rungroup) VALUES (%s, %s, %s, %s)"
    update = "UPDATE runorder SET cars=%s,modified=now() WHERE eventid=%s and course=%s and rungroup=%s"

    # Add a second run order and sync
    with syncx['A'].cursor() as cur:
        cur.execute(update, ([syncdata.carid2], syncdata.eventid, 1, 1))
        syncx['A'].commit()

        # make sure we can add to another course but not another rungroup with the same event/course
        cur.execute(insert, ([syncdata.carid2], syncdata.eventid, 2, 2))
        with pytest.raises(psycopg2.InternalError):
            cur.execute(insert, ([syncdata.carid2], syncdata.eventid, 1, 2))
        syncx['A'].rollback()

        # make sure we can't add an invalid carid
        with pytest.raises(psycopg2.InternalError):
            cur.execute(insert, ([uuid.uuid4()], syncdata.eventid, 2, 2))
        syncx['A'].rollback()


    time.sleep(0.1)
    dosync(syncx['A'], mergex['A'])

    # Simulate a runorder reorder
    with syncx['A'].cursor() as cur:
        cur.execute(update, ([syncdata.carid2, syncdata.carid], syncdata.eventid, 1, 1))
        syncx['A'].commit()
    time.sleep(0.1)

    # Different reorder on B
    with syncx['B'].cursor() as cur:
        cur.execute(update, ([syncdata.carid3, syncdata.carid2, syncdata.carid], syncdata.eventid, 1, 1))
        syncx['B'].commit()

    time.sleep(0.1)
    dosync(syncx['A'], mergex['A'])

    verify_runorder(syncx, (syncdata.eventid, 1, 1), (('cars', [syncdata.carid3, syncdata.carid2, syncdata.carid]),))


def test_classorder_reorder(syncdbs, syncdata):
    syncx, mergex = syncdbs

    insert = "INSERT INTO classorder (eventid, rungroup, classes, modified) VALUES (%s, %s, %s, now())"
    update = "UPDATE classorder SET classes=%s, modified=now() WHERE eventid=%s AND rungroup=%s"

    # Add a second run order row and sync
    with syncx['A'].cursor() as cur:
        cur.execute(insert, (syncdata.eventid, 1, ["c3", "c2", "c1"]))
        syncx['A'].commit()

        # can't add to another group in same event
        with pytest.raises(psycopg2.InternalError):
            cur.execute(insert, (syncdata.eventid, 2, ["c3", "c4", "c5"]))
        syncx['A'].rollback()

        # can't add if class doesn't exist
        with pytest.raises(psycopg2.InternalError):
            cur.execute(insert, (syncdata.eventid, 2, ["c6"]))
        syncx['A'].rollback()

    time.sleep(0.1)
    dosync(syncx['A'], mergex['A'])

    # Simulate a classorder reorder
    with syncx['A'].cursor() as cur:
        cur.execute(update, (["c2", "c3", "c1"], syncdata.eventid, 1))
        syncx['A'].commit()
    time.sleep(0.1)

    # Different reorder on B
    with syncx['B'].cursor() as cur:
        cur.execute(update, (["c1", "c2", "c3"], syncdata.eventid, 1))
        syncx['B'].commit()

    time.sleep(0.1)
    dosync(syncx['A'], mergex['A'])

    verify_classorder(syncx, (syncdata.eventid, 1), (('classes', ['c1', 'c2', 'c3']),))
