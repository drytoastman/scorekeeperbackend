from datetime import datetime
import json
import logging
import uuid

from flask import g
from .base import AttrBase

log = logging.getLogger(__name__)

class Event(AttrBase):
    TABLENAME = "events"

    def delete(self):
        """ delete registrations and the event itself, if there are runs or other references, it will throw an IntegrityError """
        with g.db.cursor() as cur:
            cur.execute("delete from registered where eventid=%s", (self.eventid,))
            cur.execute("delete from events where eventid=%s", (self.eventid,))
        g.db.commit()

    def feedFilter(self, key, value):
        if key in ('payments', 'snail'):
            return None
        return value

    def getCountedRuns(self):
        ret = getattr(self, 'counted', 0)
        if ret <= 0:
            return 999
        return ret

    def paymentRequired(self): return self.attr.get('paymentreq', False)
    def hasOpened(self): return datetime.utcnow() > self.regopened
    def hasClosed(self): return datetime.utcnow() > self.regclosed
    def isOpen(self):    return self.hasOpened() and not self.hasClosed()

    def getRegisteredCount(self):
        if self.paymentRequired(): 
            return self.getval("SELECT count(r.carid) FROM registered r JOIN payments p ON r.eventid=p.eventid and r.carid=p.carid WHERE r.eventid=%s", (self.eventid,))
        else:
            return self.getval("SELECT count(carid) FROM registered WHERE eventid=%s", (self.eventid,))

    def getRegisteredDriverCount(self):
        if self.paymentRequired():
            return self.getval("SELECT count(distinct(c.driverid)) FROM registered r JOIN payments p ON r.eventid=p.eventid and r.carid=p.carid JOIN cars c ON r.carid=c.carid WHERE r.eventid=%s", (self.eventid,))
        else:
            return self.getval("SELECT count(distinct(c.driverid)) FROM registered r JOIN cars c ON r.carid=c.carid WHERE r.eventid=%s", (self.eventid,))

    @classmethod
    def new(cls):
        event = cls()
        event.eventid = uuid.uuid1()
        event.name = ""
        event.date = datetime.today()
        event.regopened = datetime.today().replace(minute=0)
        event.regclosed = datetime.today().replace(minute=0)
        event.courses = 1
        event.runs = 4
        event.countedruns = 0
        event.segments = 0
        event.perlimit = 2
        event.sinlimit = 0
        event.totlimit = 0
        event.conepen = 2.0
        event.gatepen = 10.0
        event.accountid = None
        event.ispro = False
        event.ispractice = False
        return event

    @classmethod
    def get(cls, eventid):
        return cls.getunique("select * from events where eventid=%s", (eventid,))

    @classmethod
    def byDate(cls):
        return cls.getall("select * from events order by date")


