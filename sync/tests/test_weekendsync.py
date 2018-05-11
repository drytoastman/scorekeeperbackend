#!/usr/bin/env python3

import json
import datetime
import time
import uuid

from helpers import *

def test_weekendsync(syncdbs, syncdata):
    """ Dealing with the advanced merge on the driver table """
    syncx, mergex = syncdbs
    id1 = uuid.uuid1()
    id2 = uuid.uuid1()

    # syncx['A']: insert weekend 1
    with syncx['A'].cursor() as cur:
        s = datetime.date.today()
        e = s + datetime.timedelta(days=5)
        cur.execute("INSERT INTO weekendmembers (uniqueid, membership, driverid, startdate, enddate, issuer, issuermem, region, area) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (id1, 111111, syncdata.driverid, s, e, 'Some Name', '09876', 'NWR', 'autocross'))
                                            
        syncx['A'].commit()
    time.sleep(0.1)

    dosync(syncx['A'], mergex['A'])
    verify_weekend(syncx, id1, (('membership', 111111),))
    verify_weekend(syncx, id2, None)

    # syncx['B']: insert weekend 2, delete weekend 1
    with syncx['B'].cursor() as cur:
        s = datetime.date.today()
        e = s + datetime.timedelta(days=5)
        cur.execute("INSERT INTO weekendmembers (uniqueid, membership, driverid, startdate, enddate, issuer, issuermem, region, area) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (id2, 222222, syncdata.driverid, s, e, 'Some Name', '09876', 'NWR', 'autocross'))
        cur.execute("DELETE FROM weekendmembers WHERE uniqueid=%s", (id1,))
        syncx['B'].commit()
    time.sleep(0.1)

    dosync(syncx['A'], mergex['A'])
    verify_weekend(syncx, id1, None)
    verify_weekend(syncx, id2, (('membership', 222222),))

