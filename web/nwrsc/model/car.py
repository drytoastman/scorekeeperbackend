import json
import logging
import uuid

from flask import g
from .base import AttrBase

log = logging.getLogger(__name__)

class Car(AttrBase):
    TABLENAME = "cars"

    def newWCheck(self, driverid):
        """ Insert with verification that the car belongs to the logged in user """
        with g.db.cursor() as cur:
            newid = uuid.uuid1()
            self.cleanAttr()
            cur.execute("INSERT INTO cars (carid,driverid,classcode,indexcode,number,useclsmult,attr) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (newid, driverid, self.classcode, self.indexcode, self.number, self.useclsmult, json.dumps(self.attr)))
            g.db.commit()

    def updateWCheck(self, verifyid):
        """ Update with verification that the car belongs to the logged in user """
        with g.db.cursor() as cur:
            self.cleanAttr()
            cur.execute("UPDATE cars SET classcode=%s,indexcode=%s,number=%s,useclsmult=%s,attr=%s,modified=now() where carid=%s and driverid=%s",
                       (self.classcode, self.indexcode, self.number, self.useclsmult, json.dumps(self.attr), 
                        self.carid, verifyid))
            g.db.commit()

    def loadActivity(self):
        self.activity = Car.getval("SELECT COUNT(ids) FROM (SELECT distinct(eventid) FROM registered WHERE carid=%s UNION SELECT distinct(eventid) FROM runs WHERE carid=%s) AS ids ", (self.carid, self.carid))

    @classmethod
    def deleteById(cls, carid):
        with g.db.cursor() as cur:
            cur.execute("DELETE FROM cars WHERE carid=%s", (carid,))
            g.db.commit()
            return cur.rowcount

    @classmethod
    def deleteByClass(cls, codes):
        with g.db.cursor() as cur:
            cur.execute("DELETE FROM cars WHERE classcode IN %s AND carid NOT IN " + 
                        "(SELECT carid FROM runs UNION SELECT carid FROM registered UNION SELECT carid FROM payments UNION SELECT carid FROM challengeruns)",
                        (codes,))
            g.db.commit()
            return cur.rowcount

    @classmethod
    def deleteWCheck(cls, carid, verifyid):
        with g.db.cursor() as cur:
            cur.execute("DELETE FROM cars WHERE carid=%s and driverid=%s", (carid, verifyid))
            g.db.commit()
            return cur.rowcount

    @classmethod
    def getForDriver(cls, driverid):
        return cls.getall("select * from cars where driverid=%s order by classcode,number", (driverid,))

    @classmethod
    def usedNumbers(cls, driverid, classcode, superunique=False):
        with g.db.cursor() as cur:
            if superunique:
                cur.execute("select distinct number from cars where number not in (select number from cars where driverid = %s)", driverid)
            else:
                cur.execute("select distinct number from cars where classcode=%s and number not in (select number from cars where classcode=%s and driverid=%s)", (classcode, classcode, driverid))
            return [x[0] for x in cur.fetchall()]

