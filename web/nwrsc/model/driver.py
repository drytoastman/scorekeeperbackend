import uuid
import json

from flask import current_app, g
from .base import AttrBase

class Driver(AttrBase):
    TABLENAME = "drivers"

    @classmethod
    def get(cls, driverid):
        return cls.getunique("SELECT * FROM drivers WHERE driverid=%s", (driverid,))

    @classmethod
    def getAll(cls):
        return cls.getall("SELECT * FROM drivers order by lower(lastname), lower(firstname)")

    @classmethod
    def getAllForSeries(cls):
        return cls.getall("SELECT distinct(d.driverid), d.firstname, d.lastname FROM drivers d JOIN cars c ON c.driverid=d.driverid JOIN runs r ON r.carid=c.carid")

    @classmethod
    def byUsername(cls, username):
        return cls.getunique("SELECT * FROM drivers WHERE username=%s", (username.strip(),))
    
    @classmethod
    def byNameEmail(cls, first, last, email):
        return cls.getunique("SELECT * FROM drivers WHERE lower(firstname)=%s AND lower(lastname)=%s AND lower(email)=%s",
                                    (first.lower().strip(), last.lower().strip(), email.lower().strip()))
    
    @classmethod
    def find(cls, first, last):
        return cls.getall("SELECT * FROM drivers WHERE lower(firstname)=%s and lower(lastname)=%s", (first.strip().lower(), last.strip().lower()))

    @classmethod
    def new(cls, first, last, email, user, password):
        with g.db.cursor() as cur:
            newid = uuid.uuid1()
            hashedpw = current_app.hasher.generate_password_hash(password).decode('utf-8')
            cur.execute("INSERT INTO drivers (driverid,firstname,lastname,email,username,password) "
                        "VALUES (%s,%s,%s,%s,%s,%s)", (newid, first, last, email, user, hashedpw))
            g.db.commit()
            return newid

    @classmethod
    def merge(cls, oldids, destid):
        with g.db.cursor() as cur:
            for srcid in oldids:
                cur.execute("UPDATE cars SET driverid=%s,modified=now() WHERE driverid=%s", (destid, srcid))
                cur.execute("DELETE FROM drivers WHERE driverid=%s", (srcid,))
            g.db.commit()

    @classmethod
    def deleteById(cls, driverid):
        with g.db.cursor() as cur:
            cur.execute("DELETE FROM cars WHERE driverid=%s", (driverid,))
            cur.execute("DELETE FROM drivers WHERE driverid=%s", (driverid,))
            g.db.commit()
            return cur.rowcount

    @classmethod
    def updatepassword(cls, driverid, username, password):
        with g.db.cursor() as cur:
            hashedpw = current_app.hasher.generate_password_hash(password).decode('utf-8')
            cur.execute("UPDATE drivers SET username=%s,password=%s,modified=now() WHERE driverid=%s", (username, hashedpw, driverid))
            g.db.commit()

    @classmethod
    def activecars(cls, driverid):
        with g.db.cursor() as cur:
            cur.execute("SELECT r.carid,r.eventid FROM runs r JOIN cars c on r.carid=c.carid WHERE c.driverid=%s union select r2.carid,r2.eventid from registered r2 JOIN cars c2 on r2.carid=c2.carid WHERE c2.driverid=%s", (driverid, driverid))
            return [(r['carid'], r['eventid']) for r in cur.fetchall()]

    @property
    def seriesattr(self):
        if not hasattr(self, '_seriesattr'):
            self._seriesattr =  self.getval("SELECT attr FROM seriesattr WHERE driverid=%s", (self.driverid,)) or {}
        return self._seriesattr

    def setSeriesAttr(self, key, val): #o'rulesack', True)
        with g.db.cursor() as cur:
            cur.execute("INSERT INTO seriesattr (driverid, attr) VALUES (%s, %s) ON CONFLICT (driverid) DO UPDATE SET attr=seriesattr.attr||%s, modified=now()", (self.driverid, {key:val}, {key:val}))
            g.db.commit()

