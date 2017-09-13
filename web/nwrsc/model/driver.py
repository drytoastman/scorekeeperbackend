import uuid
import json

from flask import g
from .base import AttrBase

class Driver(AttrBase):
    TABLENAME = "drivers"

    @classmethod
    def get(cls, driverid):
        return cls.getunique("SELECT * FROM drivers WHERE driverid=%s", (driverid,))

    @classmethod
    def getAll(cls):
        return cls.getall("SELECT * FROM drivers")

    @classmethod
    def byusername(cls, username):
        return cls.getunique("SELECT * FROM drivers WHERE username=%s", (username.strip(),))

    @classmethod
    def find(cls, first, last):
        return cls.getall("SELECT * FROM drivers WHERE lower(firstname)=%s and lower(lastname)=%s", (first.strip().lower(), last.strip().lower()))

    @classmethod
    def new(cls, first, last, email, user, pwhash):
        with g.db.cursor() as cur:
            newid = uuid.uuid1()
            cur.execute("INSERT INTO drivers (driverid,firstname,lastname,email,username,password) "
                        "VALUES (%s,%s,%s,%s,%s,%s)", (newid, first, last, email, user, pwhash))
            g.db.commit()
            return newid

    @classmethod
    def updatepassword(cls, driverid, username, password):
        with g.db.cursor() as cur:
            cur.execute("UPDATE drivers SET username=%s,password=%s,modified=now() WHERE driverid=%s", (username, password, driverid))
            g.db.commit()

    @classmethod
    def activecars(cls, driverid):
        with g.db.cursor() as cur:
            cur.execute("SELECT r.carid,r.eventid FROM runs r JOIN cars c on r.carid=c.carid WHERE c.driverid=%s union select r2.carid,r2.eventid from registered r2 JOIN cars c2 on r2.carid=c2.carid WHERE c2.driverid=%s", (driverid, driverid))
            return [(r['carid'], r['eventid']) for r in cur.fetchall()]


