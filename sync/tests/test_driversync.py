#!/usr/bin/env python3

import json
import time

def test_driversync(syncdbs, syncdata):
    (synca, syncb, merge) = syncdbs

    # Modify firstname and address on A
    with synca.cursor() as cur:
        cur.execute("UPDATE drivers SET firstname=%s,attr=%s,modified=now() where driverid=%s", ('newfirst', json.dumps({'address': '123'}), syncdata.driverid,))
        synca.commit()
    time.sleep(0.1)

    # Modify lastname and zip on B
    with syncb.cursor() as cur:
        cur.execute("UPDATE drivers SET lastname=%s,attr=%s,modified=now() where driverid=%s", ('newlast', json.dumps({'zip': '98111'}), syncdata.driverid,))
        syncb.commit()
    time.sleep(0.1)

    # Modify email and zip on A
    with synca.cursor() as cur:
        cur.execute("UPDATE drivers SET email=%s,attr=%s,modified=now() where driverid=%s", ('newemail', json.dumps({'address': '123', 'zip': '98222'}), syncdata.driverid,))
    time.sleep(0.1)

    sync_and_verify_driver(synca, syncb, merge, syncdata.driverid,
        (('firstname', 'newfirst'), ('lastname', 'newlast'), ('email', 'newemail')),
        (('address', '123'), ('zip', '98222')))

    # Delete zip
    with synca.cursor() as cur:
        cur.execute("UPDATE drivers SET attr=%s,modified=now() where driverid=%s", (json.dumps({'address': '123'}), syncdata.driverid,))
    time.sleep(0.1)

    sync_and_verify_driver(synca, syncb, merge, syncdata.driverid,
        (('firstname', 'newfirst'), ('lastname', 'newlast'), ('email', 'newemail')),
        (('address', '123'), ('zip', None)))


def sync_and_verify_driver(synca, syncb, merge, driverid, coltuple, attrtuple):
    # Sync and then load drivers from both sides and verify that they are as intended
    with synca.cursor() as cura, syncb.cursor() as curb:
        cura.execute("UPDATE mergeservers SET lastcheck='epoch', nextcheck='epoch'")
        synca.commit()
        merge.runonce()
        cura.execute("SELECT *  FROM drivers WHERE driverid=%s", (driverid,))
        curb.execute("SELECT *  FROM drivers WHERE driverid=%s", (driverid,))
        da = cura.fetchone()
        db = curb.fetchone()

    for key, expected in coltuple: 
        assert da[key] == expected
    for key, expected in attrtuple: 
        assert da['attr'].get(key, None) == expected

