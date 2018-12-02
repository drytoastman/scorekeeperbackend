import collections
import datetime
import logging
import operator
import re
from flask import g

from .base import AttrBase

log = logging.getLogger(__name__)

class Series(object):
    ACTIVE   = 1
    ARCHIVED = 0
    INVALID  = -1
    UNKNOWN  = -2

    @classmethod
    def type(cls, series):
        with g.db.cursor() as cur:
            cur.execute("select schema_name from information_schema.schemata where schema_name=%s", (series,))
            if cur.rowcount > 0: return Series.ACTIVE
            cur.execute("select count(1) from results where series=%s", (series,))
            if cur.fetchone()[0] >= 2: return Series.ARCHIVED
        return Series.INVALID

    @classmethod
    def active(cls):
        with g.db.cursor() as cur:
            cur.execute("select schema_name from information_schema.schemata")
            return [x[0] for x in cur.fetchall() if not x[0].startswith('pg_') and x[0] not in ('information_schema', 'public', 'template')]

    @classmethod
    def emailListIds(cls):
        allseries = cls.active()
        allids = set()
        with g.db.cursor() as cur:
            for s in cls.active():
                cur.execute("select val from {}.settings where name='emaillistid'".format(s))
                for row in cur.fetchall():
                    allids.add(row['val'])
        allids.discard('')
        allids.discard(None)
        return allids

    @classmethod
    def getYear(cls, series):
        try:
            return re.search('\d{4}', series).group(0)
        except:
            return "Other"

    @classmethod
    def byYear(cls):
        with g.db.cursor() as cur:
            cur.execute("select schema_name from information_schema.schemata union select series from results")
            serieslist = [x[0] for x in cur.fetchall() if x[0] not in ('pg_catalog', 'information_schema', 'public', 'template')]

            lists = collections.defaultdict(list)
            for series in serieslist:
                lists[cls.getYear(series)].append(series)

            ret = collections.OrderedDict()
            for key in sorted(lists.keys(), reverse=True):
                ret[key] = sorted(lists[key])
            if "Other" in ret:
                ret.move_to_end("Other")
            return ret


    @classmethod
    def _verifySeriesName(cls, series):
        """ We have to resort to string formatting for some operations below, filter out evil data here """
        if re.search(r'[^A-Za-z0-9]', series): raise Exception("Series has non ascii characters")
        if len(series) > 16:                   raise Exception("Series name is too long (16 characters max)")
        return True

    @classmethod
    def copySeries(cls, host, port, series, password, csettings, cclasses, ccars):
        """ Create a new series and copy over from info from the current.  """
        cls._verifySeriesName(series)
        cls._verifySeriesName(g.series)
        if Series.type(series) != Series.INVALID: raise Exception("{} already exists".format(series))
        with AttrBase.connect(host=host, port=port, user="postgres") as db:
            with db.cursor() as cur:
                cur.execute("select verify_user(%s, %s)", (series, password))
                cur.execute("select verify_series(%s)", (series,))
                if csettings:
                    cur.execute("insert into {}.settings (select * from {}.settings)".format(series, g.series))
                if cclasses:
                    cur.execute("insert into {}.indexlist (select * from {}.indexlist)".format(series, g.series))
                    cur.execute("insert into {}.classlist (select * from {}.classlist)".format(series, g.series))
                    if ccars:
                        cur.execute("insert into {}.cars (select * from {}.cars)".format(series, g.series))
                else:
                    # Need a blank index regardless of copying, fixes bug #78
                    cur.execute("insert into {}.indexlist (indexcode, descrip, value) VALUES ('', 'No Index', 1.0)".format(series))
                db.commit()

    @classmethod
    def deleteSeries(cls, host, port):
        """ Delete a series schema from the database, including the series user.  """
        cls._verifySeriesName(g.series)
        with AttrBase.connect(host=host, port=port, user="postgres") as db:
            with db.cursor() as cur:
                cur.execute("DROP SCHEMA {} CASCADE".format(g.series))
                cur.execute("DROP USER {}".format(g.series))
            db.commit()


    @classmethod
    def archivedSeriesWithin(cls, untilyear):
        allseries = Series.byYear()
        activeseries = Series.active()
        thisyear = datetime.date.today().year
        ret = list()
        for year, serieslist in allseries.items():
            try:    seriesyear = int(year)
            except: seriesyear = thisyear
            ret.extend([s for s in serieslist if s not in activeseries and seriesyear >= untilyear])
        return ret


    @classmethod
    def _updateActivityFromArchive(cls, store, key, untilyear):
        with g.db.cursor() as cur:
            for series in Series.archivedSeriesWithin(untilyear):
                cur.execute("select data->'events' from results where name='info' and series=%s", (series,))
                events = cur.fetchone()[0]
                for e in events:
                    cur.execute("select data from results where name=%s", (e['eventid'],))
                    if cur.rowcount == 0:
                        continue
                    results = cur.fetchone()[0]
                    for code, entries in results.items():
                        for entrant in entries:
                            val = entrant[key]
                            if val in store:
                                store[val] = max(ret[val], e['date'])


    @classmethod
    def getDriverActivity(cls, untilyear):
        """ Return a dict of driverid to most recent activity """
        epoch = datetime.date(1970, 1, 1)
        ret = collections.defaultdict(lambda: epoch)
        with g.db.cursor() as cur:
            # Look through the active series
            for series in Series.active():
                cur.execute("SET search_path=%s,'public'", (series,))
                cur.execute("SELECT d.driverid, MAX(e.date) as runmax, MAX(e1.date) as regmax FROM drivers d LEFT JOIN cars c ON c.driverid=d.driverid " +
                            "LEFT JOIN runs r on r.carid=c.carid LEFT JOIN events e ON r.eventid=e.eventid "+
                            "LEFT JOIN registered r1 ON r1.carid=c.carid LEFT JOIN events e1 ON r1.eventid=e1.eventid GROUP BY d.driverid")

                for r in cur.fetchall():
                    ret[r['driverid']] = max(ret[r['driverid']], r['runmax'] or epoch, r['regmax'] or epoch)

            # Any archived series that are less than X years old (need to search JSON data)
            Series._updateActivityFromArchive(ret, 'driverid', untilyear)

        return ret


    @classmethod
    def getCarActivity(cls, untilyear):
        """ Return a dict of carid to most recent activity of cars in the given series """
        ret = dict()
        epoch = datetime.date(1970, 1, 1)
        with g.db.cursor() as cur:
            # The current series
            cur.execute("SET search_path=%s,'public'", (g.series,))
            cur.execute("SELECT MAX(e.date),c.carid FROM cars c LEFT JOIN runs r ON r.carid=c.carid LEFT JOIN events e ON r.eventid=e.eventid GROUP BY c.carid")
            for r in cur.fetchall():
                ret[r['carid']] = r['max'] or epoch

            # Any other active series
            for series in Series.active():
                cur.execute("SET search_path=%s,'public'", (series,))
                cur.execute("SELECT MAX(e.date),c.carid FROM cars c LEFT JOIN runs r ON r.carid=c.carid LEFT JOIN events e ON r.eventid=e.eventid GROUP BY c.carid")
                for r in cur.fetchall():
                    if r['carid'] in ret:
                        ret[r['carid']] = max(ret[r['carid']], r['max'] or epoch)

            # Any archived series that are less than X years old (need to search JSON data)
            Series._updateActivityFromArchive(ret, 'carid', untilyear)

        return ret

