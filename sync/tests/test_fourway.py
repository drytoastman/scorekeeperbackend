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


def _verify_updateLogOnlyChanges(syncx):
    for db in syncx:
        with syncx[db].cursor() as cur:
            cur.execute("SELECT * from publiclog where tablen='drivers' and action='U'")
            for row in cur.fetchall():
                old = row['olddata']
                new = row['newdata']

                for k in list(old['attr'].keys()):
                    old[k] = old['attr'].pop(k)
                for k in list(new['attr'].keys()):
                    new[k] = new['attr'].pop(k)

                diff = {}
                for k in new:
                    if k not in old:
                       diff[k] = (None, new[k])
                    elif old[k] != new[k]:
                       diff[k] = (old[k], new[k])

                assert(set(diff.keys()) != set(['modified']))



def test_driversync(sync4dbs, syncdata):
    """ Dealing with the advanced merge on the driver table """
    syncx, mergex = sync4dbs

    # Modify firstname and address on A
    with syncx['A'].cursor() as cur:
        cur.execute("UPDATE drivers SET firstname=%s,attr=%s,modified=now() where driverid=%s", ('newfirst', json.dumps({'address': '123'}), syncdata.driverid,))
        syncx['A'].commit()
    time.sleep(0.5)

    # Sync A to B
    dosync(syncx['A'], mergex['A'], ('B',))

    # Modify lastname and zip on B, insert some spurious log data that isn't relavant to us
    with syncx['B'].cursor() as cur:
        cur.execute("UPDATE drivers SET lastname=%s,attr=%s,modified=now() where driverid=%s", ('newlast', json.dumps({'zip': '98111'}), syncdata.driverid,))
        syncx['B'].commit()
    time.sleep(0.5)

    # Sync B to C
    dosync(syncx['B'], mergex['B'], ('C',))

    # Modify email and zip on C
    with syncx['C'].cursor() as cur:
        cur.execute("UPDATE drivers SET email=%s,attr=%s,modified=now() where driverid=%s", ('newemail', json.dumps({'address': '123', 'zip': '98222'}), syncdata.driverid,))
        syncx['C'].commit()
    time.sleep(0.5)

    # Sync C to D
    dosync(syncx['C'], mergex['C'], ('D',))

    # Modify car on D
    with syncx['D'].cursor() as cur:
        cur.execute("UPDATE cars SET number=%s,modified=now() where carid=%s", (2, syncdata.carid,))
        syncx['D'].commit()
    time.sleep(0.5)

    # Sync A to D
    dosync(syncx['A'], mergex['A'], ('D',))

    # Car is equals on A and D at this point
    verify_car({k:syncx[k] for k in ['A','D']}, syncdata.carid, (('number', 2),), ())

    # Driver should be equal on all
    verify_driver(syncx, syncdata.driverid,
        (('firstname', 'newfirst'), ('lastname', 'newlast'), ('email', 'newemail')),
        (('address', '123'), ('zip', '98222')))

    # Once more for everyone, they just update their local calculations of remote servers here
    dosync(syncx['D'], mergex['D'])
    dosync(syncx['C'], mergex['C'])
    dosync(syncx['B'], mergex['B'])
    dosync(syncx['A'], mergex['A'])

    # Now car should be equal on all
    verify_car(syncx, syncdata.carid, (('number', 2),), ())

    # And the hashes should match by this point
    _verify_updateLogOnlyChanges(syncx)
    _verify_totalhash(syncx)
