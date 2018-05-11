#!/usr/bin/env python3

import json
import time

from helpers import *

def test_driversync(sync4dbs, syncdata):
    """ Dealing with the advanced merge on the driver table """
    syncx, mergex = sync4dbs

    # Modify firstname and address on A
    with syncx['A'].cursor() as cur:
        cur.execute("UPDATE drivers SET firstname=%s,attr=%s,modified=now() where driverid=%s", ('newfirst', json.dumps({'address': '123'}), syncdata.driverid,))
        syncx['A'].commit()
    time.sleep(0.1)

    # Modify lastname and zip on B, insert some spurious log data that isn't relavant to us
    with syncx['B'].cursor() as cur:
        cur.execute("UPDATE drivers SET lastname=%s,attr=%s,modified=now() where driverid=%s", ('newlast', json.dumps({'zip': '98111'}), syncdata.driverid,))
        syncx['B'].commit()
    time.sleep(0.1)

    # Modify email and zip on C
    with syncx['C'].cursor() as cur:
        cur.execute("UPDATE drivers SET email=%s,attr=%s,modified=now() where driverid=%s", ('newemail', json.dumps({'address': '123', 'zip': '98222'}), syncdata.driverid,))
        syncx['C'].commit()
    time.sleep(0.1)

    dosync(syncx['A'], mergex['A'])
    dosync(syncx['B'], mergex['B'])
    dosync(syncx['C'], mergex['C'])
    dosync(syncx['D'], mergex['D'])

    verify_driver(syncx, syncdata.driverid,
        (('firstname', 'newfirst'), ('lastname', 'newlast'), ('email', 'newemail')),
        (('address', '123'), ('zip', '98222')))
