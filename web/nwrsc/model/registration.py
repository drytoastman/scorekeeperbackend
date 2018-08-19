from flask import g
from .base import AttrBase, Entrant

class Registration(AttrBase):
    TABLENAME = "registered"

    @classmethod
    def getForEvent(cls, eventid, paymentRequired=False):
        with g.db.cursor() as cur:
            cur.execute("SELECT d.driverid,d.firstname,d.lastname,d.email,d.barcode,d.optoutmail,c.*,r.*,r.modified as regmodified, d.attr as dattr,c.attr as cattr FROM cars c JOIN drivers d ON c.driverid=d.driverid JOIN registered r ON r.carid=c.carid WHERE r.eventid=%s ORDER BY c.number", (eventid,))
            retdict = {x['carid']:Entrant(**x, payments=[]) for x in cur.fetchall()}

            cur.execute("SELECT * FROM payments WHERE eventid=%s", (eventid,))
            for p in cur.fetchall():
                if p['carid'] in retdict:
                    retdict[p['carid']].payments.append(p)

            if paymentRequired:
                return list(filter(lambda x: len(x.payments) > 0, retdict.values()))
            else:
                return list(retdict.values())

    @classmethod
    def getForDriver(cls, driverid):
        with g.db.cursor() as cur:
            ret = cls.getall("SELECT r.* FROM registered r JOIN cars c on r.carid=c.carid WHERE c.driverid=%s", (driverid,))
            for r in ret:
                r.payments = []
                cur.execute("SELECT * FROM payments WHERE eventid=%s and carid=%s", (r.eventid, r.carid))
                for p in cur.fetchall():
                    r.payments.append(Payment(**p))
        return ret

    @classmethod
    def getForSeries(cls, series, driverid):
        return cls.getall("SELECT c.*,e.eventid,e.date,e.name FROM {}.registered r JOIN {}.cars c ON r.carid=c.carid JOIN {}.events e ON e.eventid=r.eventid WHERE c.driverid=%s ORDER BY e.date".format(series,series,series), (driverid,))

    @classmethod
    def deleteById(cls, eventid, carid):
        with g.db.cursor() as cur:
            cur.execute("DELETE FROM registered WHERE eventid=%s and carid=%s", (eventid, carid))
            g.db.commit()
            return cur.rowcount > 0

