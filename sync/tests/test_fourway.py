#!/usr/bin/env python3

import json
import logging
import time

from helpers import *

log = logging.getLogger(__name__)

def _verify_totalhash(syncx):
    hashes = {}
    for db in syncx:
        with syncx[db].cursor() as cur:
            cur.execute("SELECT hostname,mergestate from mergeservers")
            for row in cur.fetchall():
                hashes[db,row['hostname']] = row['mergestate']['testseries']['totalhash']

    ref = next(iter(hashes.values()))
    if not all(x == ref for x in hashes.values()):
        log.error("Non-matching hashes: {}".format(hashes))
        assert False

def test_driversync(sync4dbs, syncdata):
    """ Dealing with the advanced merge on the driver table """
    syncx, mergex = sync4dbs

    # Modify firstname and address on A
    with syncx['A'].cursor() as cur:
        cur.execute("UPDATE drivers SET firstname=%s,attr=%s,modified=now() where driverid=%s", ('newfirst', json.dumps({'address': '123'}), syncdata.driverid,))
        syncx['A'].commit()
    time.sleep(0.5)

    # Modify lastname and zip on B, insert some spurious log data that isn't relavant to us
    with syncx['B'].cursor() as cur:
        cur.execute("UPDATE drivers SET lastname=%s,attr=%s,modified=now() where driverid=%s", ('newlast', json.dumps({'zip': '98111'}), syncdata.driverid,))
        syncx['B'].commit()
    time.sleep(0.5)

    # Modify email and zip on C
    with syncx['C'].cursor() as cur:
        cur.execute("UPDATE drivers SET email=%s,attr=%s,modified=now() where driverid=%s", ('newemail', json.dumps({'address': '123', 'zip': '98222'}), syncdata.driverid,))
        syncx['C'].commit()
    time.sleep(0.5)

    # Modify car on D
    with syncx['D'].cursor() as cur:
        cur.execute("UPDATE cars SET number=%s,modified=now() where carid=%s", (2, syncdata.carid,))
        syncx['D'].commit()
    time.sleep(0.5)


    dosync(syncx['A'], mergex['A'])
    dosync(syncx['B'], mergex['B'])
    dosync(syncx['C'], mergex['C'])
    dosync(syncx['D'], mergex['D'])

    # Data should be equal at this point
    verify_car(syncx, syncdata.carid, (('number', 2),), ())
 
    verify_driver(syncx, syncdata.driverid,
        (('firstname', 'newfirst'), ('lastname', 'newlast'), ('email', 'newemail')),
        (('address', '123'), ('zip', '98222')))

    dosync(syncx['C'], mergex['C'])
    dosync(syncx['B'], mergex['B'])
    dosync(syncx['A'], mergex['A'])

    # And the hashes should match by this point
    _verify_totalhash(syncx)


