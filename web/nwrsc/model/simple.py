from collections import defaultdict
import datetime
import json
import logging
import operator
import uuid

from flask import g
from .base import AttrBase, Entrant

log = logging.getLogger(__name__)

class Attendance(object):

    @classmethod
    def getAll(cls):
        with g.db.cursor() as cur:
            cur.execute("SELECT distinct(d.driverid), lower(d.firstname) AS firstname, lower(d.lastname) AS lastname FROM runs r JOIN cars c ON r.carid=c.carid JOIN drivers d ON c.driverid=d.driverid "+
                        " ORDER BY lower(d.lastname), lower(d.firstname)")
            return [Entrant(**x) for x in cur.fetchall()]

    @classmethod
    def forEvent(cls, event):
        with g.db.cursor() as cur:
            cur.execute("SELECT distinct(d.driverid), lower(d.firstname) AS firstname, lower(d.lastname) AS lastname FROM runs r JOIN cars c ON r.carid=c.carid JOIN drivers d ON c.driverid=d.driverid " +
                        "WHERE r.eventid=%s " +
                        "ORDER BY lower(d.lastname), lower(d.firstname)", (event.eventid,))
            return [Entrant(**x) for x in cur.fetchall()]

    @classmethod
    def newForEvent(cls, event):
        with g.db.cursor() as cur:
            cur.execute("SELECT distinct(d.driverid), lower(d.firstname) AS firstname, lower(d.lastname) AS lastname FROM runs r JOIN cars c ON r.carid=c.carid JOIN drivers d ON c.driverid=d.driverid " +
                        "WHERE r.eventid=%s AND d.driverid NOT IN (SELECT d.driverid FROM runs r JOIN cars c ON r.carid=c.carid JOIN drivers d ON c.driverid=d.driverid WHERE r.eventid IN "+
                                                                       "(SELECT eventid from events where date < %s)) ORDER BY lower(d.lastname), lower(d.firstname)", (event.eventid, event.date))
            return [Entrant(**x) for x in cur.fetchall()]

    @classmethod
    def getActivity(cls):
        ret = defaultdict(Entrant)
        with g.db.cursor() as cur:
            cur.execute("SELECT distinct(d.driverid), d.firstname, d.lastname, d.email, d.optoutmail, d.barcode, r.eventid, c.classcode FROM runs r JOIN cars c ON r.carid=c.carid JOIN drivers d ON c.driverid=d.driverid")
            for row in cur.fetchall():
                e = ret.setdefault(row['driverid'], Entrant(**row, runs=defaultdict(list), reg=defaultdict(list)))
                e.runs[str(row['eventid'])].append(row['classcode'])
            cur.execute("SELECT distinct(d.driverid), d.firstname, d.lastname, d.email, d.optoutmail, d.barcode, r.eventid, c.classcode FROM registered r JOIN cars c ON r.carid=c.carid JOIN drivers d ON c.driverid=d.driverid")
            for row in cur.fetchall():
                e = ret.setdefault(row['driverid'], Entrant(**row, runs=defaultdict(list), reg=defaultdict(list)))
                e.reg[str(row['eventid'])].append(row['classcode'])
        return ret


class Audit(object):

    @classmethod
    def audit(cls, event, course, group):
        with g.db.cursor() as cur:
            cur.execute("SELECT cars FROM runorder WHERE eventid=%s AND course=%s AND rungroup=%s", (event.eventid, course, group))
            if not cur.rowcount:
                return list()
            order = cur.fetchone()[0]
            log.warning(order)
            cur.execute("SELECT d.firstname,d.lastname,c.* FROM cars c JOIN drivers d ON c.driverid=d.driverid WHERE carid IN %s", (tuple(order), ))
            hold = dict()
            for res in [Entrant(**x) for x in cur.fetchall()]:
                res.runs = [None] * event.runs
                hold[res.carid] = res

            if not hold:
                return list()

            cur.execute("SELECT * FROM runs WHERE eventid=%s and course=%s and carid in %s", (event.eventid, course, tuple(hold.keys())))
            for run in [Run(**x) for x in cur.fetchall()]:
                res = hold[run.carid]
                if run.run > event.runs:
                    res.runs[:] =  res.runs + [None]*(run.run - event.runs)
                res.runs[run.run-1] = run

            return list([hold[x] for x in order])


class Challenge(AttrBase):

    @classmethod
    def getAll(cls):
        return cls.getall("select * from challenges order by challengeid")


class EmailQueue(object):

    @classmethod
    def queueMessage(self, **kwargs):
        with g.db.cursor() as cur:
            cur.execute("INSERT INTO emailqueue (content) VALUES (%s)", (json.dumps(kwargs),))
        g.db.commit()


class EventStream(object):

    @classmethod
    def get(self, timestamp):
        """ If the last recorded event is > timestamp, get the last 30 """
        ret = list()
        with g.db.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM localeventstream WHERE time > %s", (timestamp,))
            val = cur.fetchone()[0]
            if val == 0:
                return ret

            cur.execute("SELECT * FROM localeventstream ORDER BY time DESC LIMIT 30")
            for row in cur.fetchall():
                ret.append(row)

        ret.sort(key=lambda e: e['time'])
        return ret


class ExternalResult(AttrBase):
    TABLENAME = "externalresults"

    @classmethod
    def getAll(cls, eventid):
        return cls.getall("SELECT r.*,d.firstname,d.lastname FROM drivers d JOIN externalresults r ON r.driverid=d.driverid WHERE r.eventid=%s", (eventid,))


class NumberEntry(AttrBase):
    @classmethod
    def allNumbers(cls):
        with g.db.cursor() as cur:
            cur.execute("SELECT d.firstname, d.lastname, c.classcode, c.number FROM drivers d JOIN cars c ON c.driverid=d.driverid WHERE c.classcode!='HOLD'")
            return [cls(**x) for x in cur.fetchall()]


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


class PaymentSecret(AttrBase):
    TABLENAME = "paymentsecrets"


class Payment(AttrBase):
    TABLENAME = "payments"

    @classmethod
    def getAll(cls):
        return cls.getall("SELECT p.*,c.*,d.driverid,d.firstname,d.lastname,d.email,d.optoutmail,e.name,e.date FROM payments p JOIN cars c ON p.carid=c.carid JOIN drivers d ON c.driverid=d.driverid JOIN events e ON p.eventid=e.eventid ORDER BY p.txtime")


class Run(AttrBase):

    @classmethod
    def getLast(self, eventid, moddt, classcode=None, course=None):
        """ Search through serieslog rather than tables so that we can pick up deletes as well as regular insert/update """
        ret = dict()
        with g.db.cursor() as cur:
            args = [moddt, str(eventid), str(eventid)]
            filt = ""
            if classcode:
                args.append(classcode)
                filt += "AND lower(c.classcode)=lower(%s) "
            if course:
                args.extend([course, course])
                filt += "AND (s.newdata->>'course'=%s OR s.olddata->>'course'=%s) "

            cur.execute("select s.ltime, s.olddata->>'course' coursea, s.newdata->>'course' as courseb, c.carid, c.classcode from serieslog s " +
                        "JOIN cars c ON c.carid=uuid(s.newdata->>'carid') OR c.carid=uuid(s.olddata->>'carid') " +
                        "WHERE s.tablen='runs' AND s.ltime > %s AND (s.newdata->>'eventid'=%s OR s.olddata->>'eventid'=%s) " + 
                        filt + " ORDER BY s.ltime", tuple(args))
            for row in cur.fetchall():
                entry = dict(carid=row['carid'], classcode=row['classcode'], modified=row['ltime'], course=row['coursea'] or row['courseb'])
                ret[row['classcode']] = entry
                ret['last_entry']     = entry
        return ret


class RunOrder(AttrBase):

    @classmethod
    def getNextRunOrder(cls, carid, eventid, course=1):
        """ Returns a list of objects (classcode, carid) for the next cars in order after carid """
        with g.db.cursor() as cur:
            cur.execute("WITH r AS (SELECT unnest(cars) cid from runorder WHERE eventid=%s AND course=%s AND %s=ANY(cars) LIMIT 1) SELECT c.carid,c.classcode from cars c JOIN r ON r.cid=c.carid", (eventid, course, carid));
            order = [RunOrder(**x) for x in cur.fetchall()]
            ret = []
            for ii, row in enumerate(order):
                if row.carid == carid:
                    for jj in range(ii+1, ii+4):
                        ret.append(order[jj%len(order)])
                    break
            return ret


class TempCache():

    @classmethod
    def nextorder(cls):
        with g.db.cursor() as cur:
            cur.execute("SELECT nextval('ordercounter')")
            return cur.fetchone()[0]

    @classmethod
    def get(cls, key):
        with g.db.cursor() as cur:
            cur.execute("SELECT data FROM tempcache WHERE key=%s", (key, ))
            ret = cur.fetchone()
            return ret and ret[0] or None

    @classmethod
    def put(cls, key, data):
        with g.db.cursor() as cur:
            jtext = json.dumps(data)
            cur.execute("INSERT INTO tempcache (key, data) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET data=%s", (key, jtext, jtext))
            g.db.commit()

        
class TimerTimes():

    @classmethod
    def getLast(cls):
        with g.db.cursor() as cur:
            try:
                cur.execute("select raw from timertimes order by modified desc limit 1", ())
                return cur.fetchone()[0]
            except Exception as e:
                return None


class Unsubscribe():

    @classmethod
    def set(cls, driverid, listid):
        with g.db.cursor() as cur:
            cur.execute("INSERT INTO unsubscribe (driverid, emaillistid) VALUES (%s, %s) ON CONFLICT (driverid, emaillistid) DO NOTHING", (driverid, listid)) 
            g.db.commit()

    @classmethod
    def clear(cls, driverid, listid):
        with g.db.cursor() as cur:
            cur.execute("DELETE FROM unsubscribe WHERE driverid=%s and emaillistid=%s", (driverid, listid))
            g.db.commit()

    @classmethod
    def get(cls, driverid):
        with g.db.cursor() as cur:
            cur.execute("SELECT emaillistid FROM unsubscribe WHERE driverid=%s", (driverid,))
            return [row['emaillistid'] for row in cur.fetchall()]

    @classmethod
    def getUnsub(cls, listid):
        with g.db.cursor() as cur:
            cur.execute("SELECT driverid FROM unsubscribe WHERE emaillistid=%s", (listid,))
            return [row['driverid'] for row in cur.fetchall()]


class WeekendMembers():

    @classmethod
    def getAll(cls):
        with g.db.cursor() as cur:
            try:
                cur.execute("select val from settings where name='weekendregion'")
                region = cur.fetchone()['val']
                cur.execute("SELECT w.*, d.firstname, d.lastname, d.email, d.attr FROM weekendmembers w JOIN drivers d ON w.driverid=d.driverid WHERE w.region=%s ORDER BY w.membership", (region,))
                return [AttrBase(**x).getAsDict() for x in cur.fetchall()]
            except Exception as e:
                log.warning(e)
                return []

