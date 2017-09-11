
from flask import g
import logging

from .base import AttrBase

log = logging.getLogger(__name__)

class Event(AttrBase):
    TABLENAME = "events"

    def feedFilter(self, key, value):
        if key in ('payments', 'snail'):
            return None
        return value

    def getCountedRuns(self):
        ret = getattr(self, 'counted', 0)
        if ret <= 0:
            return 999
        return ret

    def hasOpened(self): return datetime.utcnow() > self.regopened
    def hasClosed(self): return datetime.utcnow() > self.regclosed
    def isOpen(self):    return self.hasOpened() and not self.hasClosed()
    def getCount(self):  return self.getval("SELECT count(carid) FROM registered WHERE eventid=%s", (self.eventid,))
    def getDriverCount(self): return self.getval("SELECT count(distinct(c.driverid)) FROM registered r JOIN cars c ON r.carid=c.carid WHERE r.eventid=%s", (self.eventid,))

    @classmethod
    def get(cls, eventid):
        return cls.getunique("select * from events where eventid=%s", (eventid,))

    @classmethod
    def byDate(cls):
        return cls.getall("select * from events order by date")


