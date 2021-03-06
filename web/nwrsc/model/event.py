from datetime import datetime
import json
import logging
import operator
import uuid

from flask import g
from .base import AttrBase
from .series import Series

log = logging.getLogger(__name__)

class Event(AttrBase):
    TABLENAME = "events"
    REGTYPES = [
        (0, 'Standard Event with Classes'),
        (1, 'AM/PM registration (no classes)'),
        (2, 'Day registration (no classes)')
    ]

    def delete(self):
        """ Override base to delete registrations and the event itself, if there are runs or other references, it will throw an IntegrityError """
        with g.db.cursor() as cur:
            cur.execute("delete from registered where eventid=%s", (self.eventid,))
            cur.execute("delete from events where eventid=%s", (self.eventid,))
        g.db.commit()

    def getCountedRuns(self):
        ret = getattr(self, 'countedruns', 0)
        if ret <= 0:
            return 999
        return ret

    def getSessions(self):
        regtype = getattr(self, 'regtype', 0)
        if   regtype == 1: return ('AM', 'PM')
        elif regtype == 2: return ('Day', )
        else: return tuple()

    def usingSessions(self):
        regtype = getattr(self, 'regtype', 0)
        return regtype != 0

    def paymentRequired(self): return self.attr.get('paymentreq', False)
    def hasOpened(self): return datetime.utcnow() > self.regopened
    def hasClosed(self): return datetime.utcnow() > self.regclosed
    def isOpen(self):    return self.hasOpened() and not self.hasClosed()

    def getRegisteredCount(self):
        if self.paymentRequired(): 
            return self.getval("SELECT count(r.carid) FROM registered r JOIN payments p ON r.eventid=p.eventid AND r.carid=p.carid AND r.session=p.session WHERE r.eventid=%s", (self.eventid,))
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
        event.regtype = 0
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
        event.isexternal = False
        event.champrequire = False
        event.useastiebreak = False
        return event

    @classmethod
    def get(cls, eventid):
        return cls.getunique("select * from events where eventid=%s", (eventid,))

    @classmethod
    def byDate(cls, ignoreexternal=False):
        return cls.getall("SELECT * FROM events {} ORDER BY date,regopened,regclosed".format(ignoreexternal and " WHERE NOT isexternal " or " ",))

    @classmethod
    def allSeriesByDate(cls, ignoreexternal=False):
        ret = list()
        for s in Series.active():
            for e in cls.getall("SELECT * FROM {}.events WHERE date >= (current_date-3) {} ORDER BY date".format(s, ignoreexternal and " WHERE NOT isexternal " or " ")):
                e.series = s
                ret.append(e)
        return sorted(ret, key=operator.attrgetter('date'))

