""" Methods used by the admin page that work across all series """

from flask import g
from .series import Series
from .base import AttrBase, UPDATES

class SuperAuth(AttrBase):

    @classmethod
    def getActivityInOtherSeries(cls, ignoreseries, driverid):
        ret = list()
        with g.db.cursor() as cur:
            for s in Series.active():
                if s == ignoreseries: continue
                cur.execute("SELECT carid FROM {}.cars WHERE driverid=%s".format(s), (driverid,))
                if cur.rowcount > 0:
                    ret.append(s)
        return ret

    @classmethod
    def getCarsForDriver(cls, driverid):
        ret = list()
        with g.db.cursor() as cur:
            for s in Series.active():
                cur.execute("SELECT * FROM {}.cars WHERE driverid=%s".format(s), (driverid,))
                for row in cur.fetchall():
                    c = cls(**row, series=s)
                    c.activity = cls.getval("SELECT COUNT(ids) FROM (SELECT distinct(eventid) FROM {}.registered WHERE carid=%s UNION SELECT distinct(eventid) FROM {}.runs WHERE carid=%s) AS ids ".format(s, s), (c.carid, c.carid))
                    ret.append(c)
        return ret

    @classmethod
    def deleteDriver(cls, driverid):
        with g.db.cursor() as cur:
            for s in Series.active():
                cur.execute("DELETE FROM {}.cars WHERE driverid=%s".format(s), (driverid,))
            cur.execute("DELETE FROM drivers WHERE driverid=%s", (driverid,))
            g.db.commit()
            return cur.rowcount

    @classmethod
    def deleteCar(cls, series, carid):
        with g.db.cursor() as cur:
            cur.execute("DELETE FROM {}.cars WHERE carid=%s".format(series), (carid,))
            g.db.commit()
            return cur.rowcount

    @classmethod
    def merge(cls, oldids, destid):
        active = Series.active()
        with g.db.cursor() as cur:
            for srcid in oldids:
                for s in active:
                    cur.execute("UPDATE {}.cars SET driverid=%s,modified=now() WHERE driverid=%s".format(s), (destid, srcid))
                cur.execute("DELETE FROM drivers WHERE driverid=%s", (srcid,))
            g.db.commit()

    @classmethod
    def updateCar(self, series, car):
        with g.db.cursor() as cur:
            car.cleanAttr()
            cur.execute(UPDATES[car.TABLENAME].replace("UPDATE cars", "UPDATE {}.cars".format(series)), car.__dict__)
            g.db.commit()

