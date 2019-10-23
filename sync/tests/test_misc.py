#!/usr/bin/env python3

import datetime
import time
import uuid

from helpers import *

def test_accountdelete(syncdbs, syncdata):
    """ Regression test for bug where delete of payment account was being reinserted by a remote sync """
    syncx, mergex = syncdbs
    testaccountid  = 'paypalid'
    testitemid = '00000000-0000-0000-0000-000000000255',

    # Insert remote
    with syncx['B'].cursor() as cur:
        cur.execute("INSERT INTO paymentaccounts (accountid, name, type, attr) VALUES (%s, 'accountname', 'paypal', '{}')", (testaccountid,))
        cur.execute("INSERT INTO paymentitems    (itemid, accountid, name, price, currency) VALUES (%s, %s, 'itemname', 100, 'USD')", (testitemid, testaccountid))
        syncx['B'].commit()
    time.sleep(0.5)

    dosync(syncx['A'], mergex['A'])
    verify_account(syncx, testaccountid, (('name', 'accountname'), ('type', 'paypal')))
    verify_item(syncx, testitemid, (('accountid', testaccountid), ('name', 'itemname'), ('price', 100)))

    # Delete remote
    with syncx['B'].cursor() as cur:
        cur.execute("DELETE FROM paymentitems WHERE accountid=%s", (testaccountid,))
        cur.execute("DELETE FROM paymentaccounts WHERE accountid=%s", (testaccountid,))
        syncx['B'].commit()
    time.sleep(0.5)

    dosync(syncx['A'], mergex['A'])
    verify_account(syncx, testaccountid, None)
    verify_item(syncx, testitemid, None)


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

