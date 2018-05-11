#!/usr/bin/env python3

import json
import datetime
import time
import uuid

from helpers import *

def test_weekendsync(syncdbs, syncdata):
    """ Dealing with the advanced merge on the driver table """
    (synca, syncb, merge) = syncdbs
    id1 = uuid.uuid1()
    id2 = uuid.uuid1()

    # synca: insert weekend 1
    with synca.cursor() as cur:
        s = datetime.date.today()
        e = s + datetime.timedelta(days=5)
        cur.execute("INSERT INTO weekendmembers (uniqueid, membership, driverid, startdate, enddate, issuer, issuermem, region, area) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (id1, 111111, syncdata.driverid, s, e, 'Some Name', '09876', 'NWR', 'autocross'))
                                            
        synca.commit()
    time.sleep(0.1)

    dosync(synca, merge)
    verify_weekend(synca, syncb, id1, (('membership', 111111),))
    verify_weekend(synca, syncb, id2, None)

    # syncb: insert weekend 2, delete weekend 1
    with syncb.cursor() as cur:
        s = datetime.date.today()
        e = s + datetime.timedelta(days=5)
        cur.execute("INSERT INTO weekendmembers (uniqueid, membership, driverid, startdate, enddate, issuer, issuermem, region, area) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (id2, 222222, syncdata.driverid, s, e, 'Some Name', '09876', 'NWR', 'autocross'))
        cur.execute("DELETE FROM weekendmembers WHERE uniqueid=%s", (id1,))
        syncb.commit()
    time.sleep(0.1)

    dosync(synca, merge)
    verify_weekend(synca, syncb, id1, None)
    verify_weekend(synca, syncb, id2, (('membership', 222222),))

