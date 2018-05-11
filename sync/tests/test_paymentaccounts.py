#!/usr/bin/env python3

import time

from helpers import *

def test_accountdelete(syncdbs, syncdata):
    """ Regression test for bug where delete of payment account was being reinserted by a remote sync """
    (synca, syncb, merge) = syncdbs
    testaccountid  = 'paypalid'
    testitemid = '00000000-0000-0000-0000-000000000255',

    # Insert remote 
    with syncb.cursor() as cur:
        cur.execute("INSERT INTO paymentaccounts (accountid, name, type, attr) VALUES (%s, 'accountname', 'paypal', '{}')", (testaccountid,))
        cur.execute("INSERT INTO paymentitems    (itemid, accountid, name, price, currency) VALUES (%s, %s, 'itemname', 100, 'USD')", (testitemid, testaccountid))
        syncb.commit()
    time.sleep(0.5)

    dosync(synca, merge)
    verify_account(synca, syncb, testaccountid, (('name', 'accountname'), ('type', 'paypal')))
    verify_item(synca, syncb, testitemid, (('accountid', testaccountid), ('name', 'itemname'), ('price', 100)))

    # Delete remote
    with syncb.cursor() as cur:
        cur.execute("DELETE FROM paymentitems WHERE accountid=%s", (testaccountid,))
        cur.execute("DELETE FROM paymentaccounts WHERE accountid=%s", (testaccountid,))
        syncb.commit()
    time.sleep(0.5)

    dosync(synca, merge)
    verify_account(synca, syncb, testaccountid, None)
    verify_item(synca, syncb, testitemid, None)

