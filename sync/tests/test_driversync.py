#!/usr/bin/env python3

import json
import logging
import time

from helpers import *

log = logging.getLogger(__name__)

def test_driversync(syncdbs, syncdata):
    """ Dealing with the advanced merge on the driver table """
    syncx, mergex = syncdbs
    cruft1 = dict(driverid="c2c32a70-f0fa-11e7-9c7f-5e155307955f", firstname="X")
    cruft2 = dict(driverid="c2c32a70-f0fa-11e7-9c7f-5e155307955f", firstname="Y")

    # Modify firstname and address on A
    with syncx['A'].cursor() as cur:
        cur.execute("UPDATE drivers SET firstname=%s,attr=%s,modified=now() where driverid=%s", ('newfirst', json.dumps({'address': '123'}), syncdata.driverid,))
        syncx['A'].commit()
    time.sleep(0.2)

    # Modify lastname and zip on B, insert some spurious log data that isn't relavant to us
    with syncx['B'].cursor() as cur:
        cur.execute("UPDATE drivers SET lastname=%s,attr=%s,modified=now() where driverid=%s", ('newlast', json.dumps({'zip': '98111'}), syncdata.driverid,))
        cur.execute("INSERT INTO publiclog (usern, app, tablen, action, otime, ltime, olddata, newdata) VALUES ('x', 'y', 'drivers', 'I', now(), now(), '{}', %s)", (json.dumps(cruft1),))
        time.sleep(0.1)
        cur.execute("INSERT INTO publiclog (usern, app, tablen, action, otime, ltime, olddata, newdata) VALUES ('x', 'y', 'drivers', 'U', now(), now(), %s, %s)",   (json.dumps(cruft1), json.dumps(cruft2)))
        time.sleep(0.1)
        cur.execute("INSERT INTO publiclog (usern, app, tablen, action, otime, ltime, olddata, newdata) VALUES ('x', 'y', 'drivers', 'D', now(), now(), %s, '{}')", (json.dumps(cruft2),))
        syncx['B'].commit()
    time.sleep(0.2)

    # Modify email and zip on A
    with syncx['A'].cursor() as cur:
        cur.execute("UPDATE drivers SET email=%s,attr=%s,modified=now() where driverid=%s", ('newemail', json.dumps({'address': '123', 'zip': '98222'}), syncdata.driverid,))
        syncx['A'].commit()
    time.sleep(0.2)

    dosync(syncx['A'], mergex['A'])
    verify_update_logs_only_changes(syncx)
    verify_driver(syncx, syncdata.driverid,
        (('firstname', 'newfirst'), ('lastname', 'newlast'), ('email', 'newemail')),
        (('address', '123'), ('zip', '98222')))

    # Remove zip
    with syncx['A'].cursor() as cur:
        cur.execute("UPDATE drivers SET attr=%s,modified=now() where driverid=%s", (json.dumps({'address': '123'}), syncdata.driverid,))
        syncx['A'].commit()
    time.sleep(0.2)

    dosync(syncx['A'], mergex['A'])
    verify_update_logs_only_changes(syncx)
    verify_driver(syncx, syncdata.driverid,
        (('firstname', 'newfirst'), ('lastname', 'newlast'), ('email', 'newemail')),
        (('address', '123'), ('zip', None)))

    # Delete driver on remote
    with syncx['B'].cursor() as cur:
        cur.execute("DELETE FROM registered WHERE carid in (SELECT carid FROM cars WHERE driverid=%s)", (syncdata.driverid,))
        cur.execute("DELETE FROM runorder WHERE carid in (SELECT carid FROM cars WHERE driverid=%s)", (syncdata.driverid,))
        cur.execute("DELETE FROM runs WHERE carid in (SELECT carid FROM cars WHERE driverid=%s)", (syncdata.driverid,))
        cur.execute("DELETE FROM cars WHERE driverid=%s", (syncdata.driverid,))
        cur.execute("DELETE FROM drivers WHERE driverid=%s", (syncdata.driverid,))
        syncx['B'].commit()
    time.sleep(0.2)

    dosync(syncx['A'], mergex['A'])
    verify_update_logs_only_changes(syncx)
    verify_driver(syncx, syncdata.driverid, None, None)
    verify_driver(syncx, cruft1['driverid'], None, None)

