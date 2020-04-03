import logging
import uuid

from flask import g
from .base import AttrBase

log = logging.getLogger(__name__)

class PaymentAccount(AttrBase):
    TABLENAME = "paymentaccounts"

    @classmethod
    def getAll(cls):
        return cls.getall("SELECT p.*,s.secret FROM paymentaccounts p LEFT JOIN paymentsecrets s ON s.accountid=p.accountid ORDER BY name")

    @classmethod
    def get(cls, accountid):
        """ Get the payment account and also rolls in the secret from paymentsecrets """
        if accountid is None: return None
        return cls.getunique("select p.*,s.secret from paymentaccounts p LEFT JOIN paymentsecrets s ON s.accountid=p.accountid where p.accountid=%s", (accountid, ))

    @classmethod
    def deleteById(cls, accountid):
        with g.db.cursor() as cur:
            cur.execute("update events set accountid=NULL,modified=now() where accountid=%s", (accountid, ))
            cur.execute("delete from paymentsecrets  where accountid=%s", (accountid, ))
            cur.execute("delete from paymentitems    where accountid=%s", (accountid, ))
            cur.execute("delete from paymentaccounts where accountid=%s", (accountid, ))
            g.db.commit()


class PaymentItem(AttrBase):
    TABLENAME = "paymentitems"

    @classmethod
    def getAll(cls):
        return cls.getall("SELECT * FROM paymentitems")

    @classmethod
    def getForAccount(cls, accountid):
        return cls.getall("SELECT * FROM paymentitems where accountid=%s", (accountid,))

    @classmethod
    def deleteById(cls, itemid):
        with g.db.cursor() as cur:
            cur.execute("delete from paymentitems where itemid=%s", (itemid, ))
            g.db.commit()

    @classmethod
    def deleteByAccountId(cls, accountid):
        with g.db.cursor() as cur:
            cur.execute("delete from paymentitems where accountid=%s", (accountid, ))
            g.db.commit()


class PaymentSecret(AttrBase):
    TABLENAME = "paymentsecrets"


class Payment(AttrBase):
    TABLENAME = "payments"

    @classmethod
    def getAll(cls):
        return cls.getall("SELECT p.*,c.*,d.driverid,d.firstname,d.lastname,d.email,d.optoutmail,e.name,e.date FROM payments p JOIN cars c ON p.carid=c.carid JOIN drivers d ON c.driverid=d.driverid JOIN events e ON p.eventid=e.eventid ORDER BY p.txtime")

    @classmethod
    def recordPayment(cls, eventid, refid, txtype, txid, txtime, entries):
        p         = Payment()
        p.eventid = eventid
        p.refid   = refid
        p.txtype  = txtype
        p.txid    = txid
        p.txtime  = txtime

        for entry in entries:
            p.payid    = uuid.uuid1()
            p.carid    = uuid.UUID(entry['carid'])
            p.session  = entry['session']
            p.itemname = entry['name']
            p.amount   = entry['amount']
            p.insert()