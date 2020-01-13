import dateutil.parser
import datetime
import json
import logging
import math
import types
import uuid

from flask import g
from math import ceil
from copy import copy, deepcopy
from collections import defaultdict
from operator import attrgetter, itemgetter

from .base import AttrBase, Entrant
from .classlist import ClassData
from .event import Event
from .series import Series
from .settings import Settings
from .simple import Challenge, Run
from nwrsc.lib.misc import csvlist

log = logging.getLogger(__name__)


class PosPoints(object):
    def __init__(self, settingsvalue):
        self.ppoints = csvlist(settingsvalue, int)
    def get(self, position):
        idx = position - 1
        if idx >= len(self.ppoints):
            return self.ppoints[-1]
        else:
            return self.ppoints[idx]

def marklist(lst, label):
    """ Creates an attribute for each entry in the list with the value of index+1 """
    for ii, entry in enumerate(lst):
        setattr(entry, label, ii+1)

def rawgetter(obj):
    """ When sorting raw, we need to ignore non-OK status runs """
    if obj.status == "OK":
        return obj.raw
    return 999.999


class JSONEncoder(json.JSONEncoder):
    """ Helper that calls getAsDict if available for getting json encoding """
    def default(self, o):
        if hasattr(o, 'getAsDict'):
            return o.getAsDict()
        elif isinstance(o, (set, types.GeneratorType)):
            return list(o)
        else:
            return str(o)


class Result(object):
    """ 
        Interface into the results table for cached results.  This is the primary source of information
        for the results, json and xml controllers as the data is present even if the series has been
        archived.  If the series is active and the data in the regular tables is more up to date, we 
        regenerate the values in the results table.
        Names are:
            info   - series info structure
            champ  - championship data
            [UUID] - event or challenge result data matched to that id
    """

    @classmethod
    def cacheAll(cls):
        info = cls.getSeriesInfo()
        for e in info.getEvents():
            cls.getEventResults(e.eventid)
            for c in info.getChallengesForEvent(uuid.UUID(e.eventid)):
                cls.getChallengeResults(c.challengeid)
        cls.getChampResults()

    @classmethod
    def getSeriesInfo(cls):
        name = "info"
        if cls._needUpdate(False, ('challenges', 'classlist', 'indexlist', 'events', 'settings'), name):
            cls._updateSeriesInfo(name)
        res = cls._loadResults(name)
        return SeriesInfo(res)

    @classmethod
    def getEventResults(cls, eventid):
        if cls._needEventUpdate(eventid):
            cls._updateEventResults(eventid)
        return cls._loadResults(eventid)

    @classmethod
    def getChallengeResults(cls, challengeid):
        if cls._needUpdate(True, ('challengerounds', 'challengeruns'), challengeid):
            cls._updateChallengeResults(challengeid)
        ret = dict() # note: JSON can't store using ints as keys
        for rnd in cls._loadResults(challengeid):
            ret[rnd['round']] = rnd
        return ret

    @classmethod
    def getChampResults(cls):
        """ returns a ChampClass list object """
        name = "champ"
        if cls._needUpdate(True, ('settings', 'classlist', 'indexlist', 'events', 'cars', 'runs', 'externalresults'), name):
            cls._updateChampResults(name)
        res = cls._loadResults(name)
        for k, v in res.items():
            res[k] = ChampClass(v) # Rewrap the list with ChampClass for template function
        return res

    @classmethod
    def getTopTimesTable(cls, classdata, results, *keys, **kwargs):
        """ Get top times.  Pass in results from outside as in some cases, they are already loaded """
        return cls._loadTopTimesTable(classdata, results, *keys, **kwargs)

    @classmethod
    def getTopTimesLists(cls, classdata, results, *keys, **kwargs):
        """ Get top times.  Pass in results from outside as in some cases, they are already loaded """
        return cls._loadTopTimesTable(classdata, results, *keys, wrapInClass=TopTimesListsWrapper, **kwargs)

    @classmethod
    def getDecoratedClassResults(cls, settings, eventresults, *carids, rungroup=None):
        """ Decorate the objects with old and potential results for the announcer information """
        return cls._decorateClassResults(settings, eventresults, *carids, rungroup=rungroup)

    @classmethod
    def getDecoratedChampResults(cls, champresults, *markentrants):
        """ Decorate the objects with old and potential results for the announcer information """
        return cls._decorateChampResults(champresults, *markentrants)

    @classmethod
    def getLastCourse(cls, e):
        """ Find the last course information for an entrant based on mod tags of runs """
        lasttime = dateutil.parser.parse("2000-01-01")
        lastcourse = 0
        for c in e['runs']:
            for r in c:
                mod = dateutil.parser.parse(r.get('modified', '2000-01-02')) # Catch JSON placeholders
                if mod > lasttime:
                    lasttime = mod
                    lastcourse = r['course']
        return lastcourse

    @classmethod
    def getBestNetRun(cls, e, course=0, norder=1):
        """ Get the best net run for last course run by an entrant
            If course is specified, overrides default of last
            If norder is specified, overrides default of 1
        """
        if course == 0:
            # Order picked (1: arg, 2: entrant key, 3: recalculate)
            course = e.get('lastcourse', cls.getLastCourse(e))
        return next((x for x in e['runs'][course-1] if x['norder'] == norder and x['status'] != 'PLC'), None)

    @classmethod
    def getLastRun(cls, e):
        """ Get the last recorded run on any course """
        course = e.get('lastcourse', cls.getLastCourse(e))
        # Separate list here to catch empty list, max doesn't like that
        runs = [x for x in e['runs'][course-1] if x['status'] != 'PLC']
        if not len(runs):
            return None
        return max(runs, key=itemgetter('run'))


    #####################  Everything below here is for internal use, use the API above ##############

    #### Helpers for basic results operations

    @classmethod
    def _needEventUpdate(cls, eventid):
        # check if we can/need to update, look for specifc eventid in data to reduce unnecessary event churn when following a single event (live)
        if g.seriestype != Series.ACTIVE:
            return False
        def row2time(rows):
            if rows: return rows[0][0]
            return datetime.datetime.fromtimestamp(0)

        with g.db.cursor() as cur:
            cur.execute("SELECT max(ltime) FROM publiclog WHERE tablen='drivers'")
            dm = row2time(cur.fetchall())
            cur.execute("SELECT max(ltime) FROM serieslog WHERE tablen IN ('settings', 'classlist', 'indexlist', 'cars')")
            sm = row2time(cur.fetchall())
            cur.execute("SELECT max(ltime) FROM serieslog WHERE tablen IN ('events', 'runs', 'externalresults') AND (olddata->>'eventid'=%s::text OR newdata->>'eventid'=%s::text)", (eventid, eventid))
            em = row2time(cur.fetchall())
            cur.execute("SELECT modified   FROM results WHERE series=%s AND name=%s::text", (g.series, eventid))
            rm = row2time(cur.fetchall())

            if rm < max(dm, sm, em):
                return True
        return False

    @classmethod
    def _needUpdate(cls, usedrivers, stables, name):
        # check if we can/need to update based on table changes
        if g.seriestype != Series.ACTIVE:
            return False
        with g.db.cursor() as cur:
            if usedrivers:
                cur.execute("select " +
                    "(SELECT MAX(times.max) FROM (SELECT max(ltime) FROM serieslog WHERE tablen IN %s UNION ALL SELECT max(ltime) FROM publiclog WHERE tablen='drivers') AS times) >" +
                    "(SELECT modified FROM results WHERE series=%s AND name=%s::text)", (stables, g.series, name))
            else:
                cur.execute("select " +
                    "(SELECT max(ltime) FROM serieslog WHERE tablen IN %s) >" +
                    "(SELECT modified FROM results WHERE series=%s AND name=%s::text)", (stables, g.series, name))
            mod = cur.fetchone()[0]
            if mod is None or mod: 
                return True
        return False

    @classmethod
    def _loadResults(cls, name):
        with g.db.cursor() as cur:
            cur.execute("select data from results where series=%s and name=%s::text", (g.series, name))
            res = cur.fetchone()
            if res is not None:
                return res['data']
            else:
                return dict()

    @classmethod
    def _insertResults(cls, name, data):
        # Get access for modifying series rows, check if we need to insert a default first.
        # Don't upsert as we have to specify LARGE json object twice.
        with g.db.cursor() as cur:
            cur.execute("set role %s", (g.series,))
            cur.execute("insert into results values (%s, %s, '{}', now()) ON CONFLICT (series, name) DO NOTHING", (g.series, name))
            cur.execute("update results set data=%s, modified=now() where series=%s and name=%s::text", (JSONEncoder().encode(data), g.series, name))
            cur.execute("reset role")
            g.db.commit()


    ### Here is where the actual data generation is done

    @classmethod
    def _updateSeriesInfo(cls, name):
        classdata = ClassData.get()
        data = {
                'events': Event.byDate(),
                'challenges': Challenge.getAll(),
                'classes': list(classdata.classlist.values()),
                'indexes': list(classdata.indexlist.values()),
                'settings': Settings.getAll()
            }
        cls._insertResults(name, data)


    @classmethod
    def _updateExternalEventResults(cls, eventid, settings, ppoints):
        """
            The external event version of _updateEventResults, only do point calculation based off of net result
        """
        results = defaultdict(list)
        with g.db.cursor() as cur:
            cur.execute("SELECT r.*,d.firstname,d.lastname FROM drivers d JOIN externalresults r ON r.driverid=d.driverid WHERE r.eventid=%s", (eventid,))
            for e in [Entrant(**x, runs=[]) for x in cur.fetchall()]:
                results[e.classcode].append(e)

            # Now for each class we can sort and update position, trophy, points(both types)
            for clas in results:
                res = results[clas]
                res.sort(key=attrgetter('net'))
                for ii, e in enumerate(res):
                    e.position   = ii+1
                    e.pospoints  = ppoints.get(e.position)
                    e.diffpoints = res[0].net*100/e.net;
                    e.points     = settings.usepospoints and e.pospoints or e.diffpoints

        cls._insertResults(eventid, results)


    @classmethod
    def _updateEventResults(cls, eventid):
        """
            Creating the cached event result data for the given event.
            The event result data is {<classcode>, [<Entrant>]}.
            Each Entrant is a json object of attributes and a list of lists of Run objects ([course#][run#])
            Each Run object is regular run data with attributes like bestraw, bestnet assigned.
        """
        results = defaultdict(list)
        cptrs   = {}
    
        event     = Event.get(eventid)
        classdata = ClassData.get()
        settings  = Settings.getAll()
        ppoints   = PosPoints(settings.pospointlist)
        sessions  = event.usingSessions()

        if event.isexternal:
            return cls._updateExternalEventResults(eventid, settings, ppoints)

        with g.db.cursor() as cur:
            # Fetch all of the entrants (driver/car combo), place in class lists, save pointers for quicker access
            cur.execute("SELECT e.rungroup,c.carid,d.firstname,d.lastname,d.attr->>'scca' as scca,c.* FROM drivers d " + 
                        "JOIN cars c ON c.driverid=d.driverid INNER JOIN (select distinct carid, rungroup FROM runs WHERE eventid=%s) e ON c.carid = e.carid", (eventid,))

            for e in [Entrant(**x) for x in cur.fetchall()]:
                if e.carid in cptrs:
                    continue # ignore duplicate carids from old series

                if sessions:
                    results[e.rungroup].append(e)
                    (e.indexval,e.indexstr) = (1.0, '')
                    e.classcode = ''
                else:
                    results[e.classcode].append(e)
                    (e.indexval,e.indexstr) = classdata.getEffectiveIndex(e)

                e.runs = [[Run(course=x+1,run=y+1,raw=999.999,cones=0,gates=0,pen=999.999,net=999.999,status='PLC') for y in range(event.runs)] for x in range(event.courses)]
                cptrs[e.carid,e.rungroup] = e

            # Fetch all of the runs, calc net and assign to the correct entrant
            cur.execute("select * from runs where eventid=%s and course<=%s and run<=%s", (eventid, event.courses, event.runs))
            for r in [Run(**x) for x in cur.fetchall()]:
                if r.raw <= 0:
                    continue # ignore crap data that can't be correct
                match = cptrs[r.carid,r.rungroup]
                match.rungroup = r.rungroup
                match.runs[r.course-1][r.run - 1] = r
                penalty = (r.cones * event.conepen) + (r.gates * event.gatepen)
                if r.status != "OK":
                    r.pen = 999.999
                    r.net = 999.999
                elif settings.indexafterpenalties:
                    r.pen = r.raw + penalty
                    r.net = r.pen * match.indexval
                else:
                    r.pen = r.raw + penalty
                    r.net = (r.raw*match.indexval) + penalty

            # For every entrant, calculate their best runs (raw,net,allraw,allnet) and event sum(net)
            for e in cptrs.values():
                e.net = 0      # Best counted net overall time
                e.pen = 0      # Best counted unindexed overall time (includes penalties)
                e.netall = 0   # Best net of all runs (same as net when counted not active)
                e.penall = 0   # Best unindexed of all runs (same as pen when counted not active)
                if event.ispro:
                    e.dialraw = 0  # Best raw times (OK status) used for dialin calculations
                counted = min(classdata.getCountedRuns(e.classcode), event.getCountedRuns())

                for course in range(event.courses):
                    bestrawall = sorted(e.runs[course], key=rawgetter)
                    bestnetall = sorted(e.runs[course], key=attrgetter('net'))
                    bestraw    = sorted(e.runs[course][0:counted], key=rawgetter)
                    bestnet    = sorted(e.runs[course][0:counted], key=attrgetter('net'))
                    marklist (bestrawall, 'arorder')
                    marklist (bestnetall, 'anorder')
                    marklist (bestraw, 'rorder')
                    marklist (bestnet, 'norder')
                    e.netall += bestnetall[0].net
                    e.penall += bestnetall[0].pen
                    e.net += bestnet[0].net
                    e.pen += bestnet[0].pen
                    if event.ispro:
                        e.dialraw += bestraw[0].raw

            # Now for each class we can sort and update position, trophy, points(both types)
            for clas in results:
                res = results[clas]
                res.sort(key=attrgetter('net'))
                trophydepth = ceil(len(res) / 3.0)
                eventtrophy = sessions or classdata.eventtrophy(clas)
                for ii, e in enumerate(res):
                    e.position   = ii+1
                    e.trophy     = eventtrophy and (ii < trophydepth)
                    e.pospoints  = ppoints.get(e.position)
                    e.diffpoints = res[0].net*100/e.net;
                    e.points     = settings.usepospoints and e.pospoints or e.diffpoints
                    if ii == 0:
                        e.diff1  = 0.0
                        e.diffn  = 0.0
                    else:
                        e.diff1  = (e.net - res[0].net)/e.indexval
                        e.diffn  = (e.net - res[ii-1].net)/e.indexval

                    # Dialins for pros
                    if event.ispro:
                        e.bonusdial = e.dialraw / 2.0
                        if ii == 0:
                            e.prodiff = len(res) > 1 and e.net - res[1].net or 0.0
                            e.prodial = e.bonusdial
                        else:
                            e.prodiff = e.net - res[0].net
                            e.prodial = res[0].dialraw * res[0].indexval / e.indexval / 2.0

    
        cls._insertResults(eventid, results)

    @classmethod
    def _decorateEntrant(cls, e):
        """ Calculate things that apply to just the entrant in question (used by class and toptimes) """

        # Always work with the last run by run number (Non Placeholder), then get first and second bestnet
        e['lastcourse'] = cls.getLastCourse(e)
        lastrun = cls.getLastRun(e)
        norder1 = cls.getBestNetRun(e)
        norder2 = cls.getBestNetRun(e, norder=2)

        key = 'anorder' # norder doesn't exist when counted runs take effect

        # Can't have any improvement if we only have one run
        if norder2:
            # Note net improvement, mark what the old net would have been
            if lastrun[key] == 1 and norder2:
                lastrun['netimp'] = lastrun['net'] - norder2['net']
                norder2['oldbest'] = True
                e['oldnet'] = e['net'] - lastrun['net'] + norder2['net']
    
            # Note raw improvement over previous best run
            # This can be n=2 for overall improvement, or n=1 if only raw, not net improvement
            if lastrun[key] == 1:
                lastrun['rawimp'] = lastrun['raw'] - norder2['raw']
            else:
                lastrun['rawimp'] = lastrun['raw'] - norder1['raw']

        # If last run had penalties, add data for potential run without penalties
        if lastrun['cones'] != 0 or lastrun['gates'] != 0:
            potnet = e['net'] - norder1['net'] + (lastrun['raw'] * e['indexval'])
            if potnet < e['net']:
                e['potnet'] = potnet
                if lastrun[key] != 1:
                    lastrun['ispotential'] = True


    @classmethod
    def _decorateClassResults(cls, settings, eventresults, *carids, rungroup=None):
        """ Calculate things for the announcer/info displays """
        carids = list(map(str, carids)) # json data holds UUID as strings
        ppoints = PosPoints(settings.pospointlist)
        entrantlist = None
        drivers = dict()

        # Find the class and entrants for the results
        for clscode, entrants in eventresults.items():
            for e in entrants:
                if rungroup and e['rungroup'] != rungroup: continue
                if e['carid'] not in carids: continue
                entrantlist = entrants
                drivers[e['carid']] = e
            if entrantlist:
                break

        if not entrantlist:
            return tuple([[], []])

        # Figure out points changes for the class
        sumlist = [x['net'] for x in entrantlist]
        sumlist.remove(e['net'])

        # Return a copy so we can decorate in different ways during a single session (new websocket feed)
        decoratedlist = deepcopy(entrantlist)
        markedlist = list()

        # Decorate our copied entrants with run change information
        for e in decoratedlist:
            if not e:
                continue
            if e.get('carid', None) in carids:
                cls._decorateEntrant(e)
                e['current'] = True
                markedlist.append(e)

            if 'oldnet' in e:
                sumlist.append(e['oldnet'])
                sumlist.sort()
                position = sumlist.index(e['oldnet'])+1
                e['oldpoints'] = settings.usepospoints and ppoints.get(position) or sumlist[0]*100/e['oldnet']
                sumlist.remove(e['oldnet'])
                decoratedlist.append({'firstname':e['firstname'], 'lastname':e['lastname'], 'net':e['oldnet'], 'isold':True})
            if 'potnet' in e:
                sumlist.append(e['potnet'])
                sumlist.sort()
                position = sumlist.index(e['potnet'])+1
                e['potpoints'] = settings.usepospoints and ppoints.get(position) or sumlist[0]*100/e['potnet']
                decoratedlist.append({'firstname':e['firstname'], 'lastname':e['lastname'], 'net':e['potnet'], 'ispotential':True})

        # Mark this entrant as current, clear others if decorate is called multiple times
        decoratedlist.sort(key=itemgetter('net'))
        return tuple([decoratedlist, markedlist])


    @classmethod
    def _decorateChampResults(cls, champresults, *markentrants):
        """ Calculate things for the announcer/info displays """
        champclass = champresults.get(markentrants[0]['classcode'], None)
        if not champclass: return []
        newlist = deepcopy(champclass)

        for e in newlist:
            entrant = None
            for me in markentrants:
                if e.get('driverid', None) == me['driverid']:
                    entrant = me
                    break

            if not entrant:
                continue

            e['current'] = True
            if 'oldpoints' in entrant and entrant['oldpoints'] < entrant['points']:
                total = e['points']['total'] - entrant['points'] + entrant['oldpoints']
                newlist.append({'firstname':e['firstname'], 'lastname':e['lastname'], 'points':{'total':total}, 'isold':True})

            if 'potpoints' in entrant and entrant['potpoints'] > entrant['points']:
                total = e['points']['total'] - entrant['points'] + entrant['potpoints']
                newlist.append({'firstname':e['firstname'], 'lastname':e['lastname'], 'points':{'total':total}, 'ispotential':True})

        newlist.sort(key=lambda x: x['points']['total'], reverse=True)
        return newlist


    @classmethod
    def _updateChallengeResults(cls, challengeid):
        rounds = dict()
        with g.db.cursor() as cur:
            getrounds = "SELECT x.*, " \
                    "d1.firstname as e1fn, d1.lastname as e1ln, c1.classcode as e1cc, c1.indexcode as e1ic, " \
                    "d2.firstname as e2fn, d2.lastname as e2ln, c2.classcode as e2cc, c2.indexcode as e2ic  " \
                    "FROM challengerounds x " \
                    "LEFT JOIN cars c1 ON x.car1id=c1.carid LEFT JOIN drivers d1 ON c1.driverid=d1.driverid " \
                    "LEFT JOIN cars c2 ON x.car2id=c2.carid LEFT JOIN drivers d2 ON c2.driverid=d2.driverid " \
                    "WHERE challengeid=%s "
    
            getruns = "select * from challengeruns where challengeid=%s "
    
            cur.execute(getrounds, (challengeid,))
            for obj in [AttrBase(**x) for x in cur.fetchall()]:
                # We organize ChallengeRound in a topological structure so we do custom setting here
                rnd = AttrBase()
                rnd.challengeid  = obj.challengeid
                rnd.round        = obj.round
                rnd.winner       = 0 
                rnd.detail       = ""
                rnd.e1           = AttrBase()
                rnd.e1.carid     = obj.car1id
                rnd.e1.dial      = obj.car1dial
                rnd.e1.newdial   = obj.car1dial
                rnd.e1.firstname = obj.e1fn or ""
                rnd.e1.lastname  = obj.e1ln or ""
                rnd.e1.classcode = obj.e1cc
                rnd.e1.indexcode = obj.e1ic
                rnd.e1.left      = None
                rnd.e1.right     = None
                rnd.e2           = AttrBase()
                rnd.e2.carid     = obj.car2id
                rnd.e2.dial      = obj.car2dial
                rnd.e2.newdial   = obj.car2dial
                rnd.e2.firstname = obj.e2fn or ""
                rnd.e2.lastname  = obj.e2ln or ""
                rnd.e2.classcode = obj.e2cc
                rnd.e2.indexcode = obj.e2ic
                rnd.e2.left      = None
                rnd.e2.right     = None
                rounds[rnd.round] = rnd
    
            cur.execute(getruns, (challengeid,))
            for run in [AttrBase(**x) for x in cur.fetchall()]:
                rnd = rounds[run.round]
                if not math.isfinite(run.raw): run.raw = 999.999
                run.net = run.status == "OK" and run.raw + (run.cones * 2) + (run.gates * 10) or 999.999
                if   rnd.e1.carid == run.carid:
                    setattr(rnd.e1, run.course==1 and 'left' or 'right', run)
                elif rnd.e2.carid == run.carid:
                    setattr(rnd.e2, run.course==1 and 'left' or 'right', run)

            for rnd in rounds.values():
                #(rnd.winner, rnd.detail) = rnd.compute()
                tl = rnd.e1.left
                tr = rnd.e1.right
                bl = rnd.e2.left
                br = rnd.e2.right

                # Missing an entrant or no run data
                if rnd.e1.carid == 0 or rnd.e2.carid == 0:
                    rnd.detail = 'No matchup yet'
                    continue
                if not any([tl, tr, bl, br]):
                    rnd.detail = 'No runs taken'
                    continue

                # Some runs taken but there was non-OK status creating a default win
                topdefault = any([tl and tl.status != 'OK', tr and tr.status != 'OK'])
                botdefault = any([bl and bl.status != 'OK', br and br.status != 'OK'])

                if topdefault and botdefault:  rnd.detail = "Double default"; continue
                if topdefault: rnd.winner = 2; rnd.detail = rnd.e2.firstname + " wins by default"; continue
                if botdefault: rnd.winner = 1; rnd.detail = rnd.e1.firstname + " wins by default"; continue

                if not tl or not tr: 
                    if tl and br:   hr = (tl.net - rnd.e1.dial) - (br.net - rnd.e2.dial)
                    elif tr and bl: hr = (tr.net - rnd.e1.dial) - (bl.net - rnd.e2.dial)
                    else:           hr = 0

                    if hr > 0:   rnd.detail = '%s leads by %0.3f' % (rnd.e2.firstname, hr)
                    elif hr < 0: rnd.detail = '%s leads by %0.3f' % (rnd.e1.firstname, hr)
                    else:        rnd.detail = 'Tied at the Half'

                    continue

                # For single car rounds, we need to stop here
                if not all([tl, tr, bl, br]):
                    rnd.detail = 'In Progress'
                    continue

                # We have all the data, calculate who won
                rnd.e1.result = rnd.e1.left.net + rnd.e1.right.net - (2*rnd.e1.dial)
                rnd.e2.result = rnd.e2.left.net + rnd.e2.right.net - (2*rnd.e2.dial)
                if rnd.e1.result < 0: rnd.e1.newdial = rnd.e1.dial + (rnd.e1.result/2 * 1.5)
                if rnd.e2.result < 0: rnd.e2.newdial = rnd.e2.dial + (rnd.e2.result/2 * 1.5)

                if rnd.e1.result < rnd.e2.result: 
                    rnd.winner = 1
                    rnd.detail = "%s wins by %0.3f" % (rnd.e1.firstname, (rnd.e2.result - rnd.e1.result))
                elif rnd.e2.result < rnd.e1.result:
                    rnd.winner = 2
                    rnd.detail = "%s wins by %0.3f" % (rnd.e2.firstname, (rnd.e1.result - rnd.e2.result))
                else:
                    rnd.detail = 'Tied?'
    
        cls._insertResults(challengeid, list(rounds.values()))


    @classmethod
    def _updateChampResults(cls, name):
        """
            Create the cached result for champ results.  
            If justeventid is None, we load all event results and create the champ results.
            If justeventid is not None, we use the previous champ results and just update the event
                (saves loading/parsing all events again)
            Returns a dict of ChampClass objects
        """
        settings  = Settings.getAll()
        classdata = ClassData.get()
        events    = Event.byDate()

        completed = 0

        # Interm storage while we distribute result data by driverid
        store = defaultdict(lambda : defaultdict(ChampEntrant))
        for event in events:
            if event.ispractice: continue
            if datetime.datetime.utcnow().date() >= event.date:
                completed += 1

            eventresults = cls.getEventResults(event.eventid)
            for classcode in eventresults:
                if not classdata.champtrophy(classcode):  # class doesn't get champ trophies, ignore
                    continue
                classmap = store[classcode]
                for entrant in eventresults[classcode]:
                    classmap[entrant['driverid']].addResults(event, entrant)

        todrop   = settings.dropevents
        bestof   = max(todrop, completed - todrop)

        # Final storage where results are an ordered list rather than map
        ret = defaultdict(ChampClass)
        for classcode, classmap in store.items():
            for entrant in classmap.values():
                entrant.finalize(bestof, events)
                ret[classcode].append(entrant)
            ret[classcode].sort(key=attrgetter('points', 'tiebreakers'), reverse=True)
            ii = 1
            for e in ret[classcode]:
                if e.eventcount < settings.minevents or len(e.missingrequired) > 0:
                    e.position = ''
                else:
                    e.position = ii
                    ii += 1

        cls._insertResults(name, ret)


    @classmethod
    def _loadTopTimesTable(cls, classdata, results, *keys, **kwargs):
        """
            Generate lists on demand as there are many iterations.  Returns a TopTimesTable class
            that wraps all the TopTimesLists together.
            For each key passed in, the following values may be set:
                indexed = True for indexed times, False for penalized but raw times
                counted = True for to only included 'counted' runs and non-second run classes
                course  = 0 for combined course total, >0 for specific course
               Extra fields that have standard defaults we stick with:
                title   = A string to override the list title with
                col     = A list of column names for the table
                fields  = The fields to match to each column
        """
        lists = list()
        carid = str(kwargs.get('carid', ''))

        for key in keys:
            indexed = key.get('indexed', True)
            counted = key.get('counted', True)
            course  = key.get('course', 0)
            title   = key.get('title', None)
            cols    = key.get('cols', None)
            fields  = key.get('fields', None)

            if title is None:
                title  = "Top {}Times ({} Runs)".format(indexed and "Indexed " or "", counted and "Counted" or "All")
                if course > 0: title += " Course {}".format(course)

            if cols is None:   cols   = ['#',   'Name', 'Class',     'Index',    '',         'Time']
            if fields is None: fields = ['pos', 'name', 'classcode', 'indexstr', 'indexval', 'time']

            ttl = TopTimesList(title, cols, fields)
            for classcode in results:
                if classdata.secondruns(classcode) and counted:
                    continue

                for e in results[classcode]:
                    name="{} {}".format(e['firstname'], e['lastname'])
                    current = False

                    # For the selected car, highlight and throw in any old/potential results if available
                    if e['carid'] == carid:
                        current = True
                        ecopy = deepcopy(e)  # Make a copy so decorations stay relative to this data
                        cls._decorateEntrant(ecopy)
                        if course == 0: # don't do old/potential single course stuff at this point
                            divisor = indexed and 1.0 or ecopy['indexval']
                            if 'potnet' in ecopy:
                                ttl.append(TopTimeEntry(fields, name=name, time=ecopy['potnet']/divisor, ispotential=True))
                            if 'oldnet' in ecopy:
                                ttl.append(TopTimeEntry(fields, name=name, time=ecopy['oldnet']/divisor, isold=True))

                    # Extract appropriate time for this entrant
                    time = 999.999
                    if course > 0:
                        for r in e['runs'][course-1]:
                            if (counted and r['norder'] == 1) or (not counted and r['anorder'] == 1):
                                time = indexed and r['net'] or r['pen']
                    else:
                        if counted:
                            time = indexed and e['net'] or e['pen']
                        else:
                            time = indexed and e['netall'] or e['penall']


                    ttl.append(TopTimeEntry(fields,
                        name      = name,
                        classcode = e['classcode'],
                        indexstr  = e['indexstr'],
                        indexval  = e['indexval'],
                        time      = time,
                        current   = current
                    ))

            # Sort and set 'pos' attribute, then add to the mass table
            ttl.sort(key=attrgetter('time'))
            pos = 1
            for entry in ttl:
                if hasattr(entry, 'classcode'):
                    entry.pos = pos
                    pos += 1

            lists.append(ttl)

        if 'wrapInClass' in kwargs:
            return kwargs['wrapInClass'](*lists)
        return TopTimesTable(*lists)


###################################################################################


class SeriesInfo(dict):
    """
        We wrap the returned JSON series info data in this for easier access 
        and returning of core model objects rather than a raw dict
    """
    def __init__(self, obj):
        self.update(obj)

    def getClassData(self):
        return ClassData(self['classes'], self['indexes'])

    def getSettings(self):
        return Settings(self['settings'])

    def getEvents(self):
        return [Event(**e) for e in self['events']]

    def getEvent(self, eventid):
        for e in self['events']:
            if uuid.UUID(e['eventid']) == eventid:
                newe = Event(**e)
                newe.date = datetime.datetime.strptime(newe.date, "%Y-%m-%d")
                return newe
        return None

    def getChallengesForEvent(self, eventid):
        return [Challenge(**c) for c in self['challenges'] if uuid.UUID(c['eventid']) == eventid]

    def getChallenge(self, challengeid):
        for c in self['challenges']:
            if uuid.UUID(c['challengeid']) == challengeid:
                return Challenge(**c)
        return None


class TopTimesListsWrapper():
    def __init__(self, *lists):
        self.lists = lists

    def serial(self, index):
        return [{k:r.__dict__.get(k,"") for k in r._fields + ['current', 'ispotential','isold'] if r.__dict__.get(k,"") } for r in self.lists[index]]


class TopTimesList(list):
    """ A list of top times along with the title, column and field info """
    def __init__(self, title, cols, fields):
        self.title = title
        self.cols = cols
        self.fields = fields


class TopTimeEntry(object):
    """ A row entry in the TopTimesList """
    def __init__(self, fields, **kwargs):
        self._fields = fields
        self.__dict__.update(kwargs)

    def __iter__(self):
        """ return a set of attributes as determined by original fields """
        for f in self._fields:
            yield getattr(self, f, "")

    def __repr__(self):
        return "{}, {}".format(self._fields, self.__dict__)


class TopTimesRow(list):
    pass


class TopTimesTable(object):
    """ We need to zip our lists together ourselves (can't do it in template anymore) so we create our Table and Rows here """
    def __init__(self, *lists):
        self.titles   = list()
        self.colcount = list()
        self.cols     = list()
        self.fields   = list()
        self.rows     = list()

        for ttl in lists:
            self.addList(ttl)

    def addList(self, ttl):
        if len(ttl.cols) != len(ttl.fields):
            raise Exception('Top times columns and field arrays are not equals in size ({}, {})'.format(len(ttl.cols), len(ttl.fields)))

        self.titles.append(ttl.title)
        self.colcount.append(len(ttl.cols))
        self.cols.append(ttl.cols)
        self.fields.append(ttl.fields)

        if len(self.rows) < len(ttl):
            self.rows.extend([TopTimesRow() for x in range(len(ttl) - len(self.rows))])

        for ii in range(len(ttl)):
            self.rows[ii].append(ttl[ii])


class PointStorage(AttrBase):

    def __init__(self):
        self.events = {}
        self.total = 0
        self.drop = []
        self.usingbest = 0
        AttrBase.__init__(self)

    def get(self, eventid):
        return self.events.get(eventid, None)

    def set(self, eventid, points):
        self.events[eventid] = points

    def theory(self, eventid, points):
        save = self.events[eventid]
        self.events[eventid] = points
        self.calc(self.usingbest)
        ret = self.total
        self.events[eventid] = save
        self.calc(self.usingbest)
        return ret
        
    def calc(self, bestof):
        self.total = 0
        self.drop = []
        self.usingbest = bestof
        for ii, points in enumerate(sorted(self.events.items(), key=lambda x:x[1], reverse=True)):
            if ii < bestof:
                self.total += points[1]  # Add to total points
            else:
                self.drop.append(points[0])  # Otherwise this is a drop event, mark eventid

    # provides the comparison for sorting
    def __eq__(self, other):
        return self.total == other.total

    def __lt__(self, other):
        return self.total < other.total


class ChampEntrant(AttrBase):

    def __init__(self):
        self.points       = PointStorage()
        self.tiebreakers  = [0]*11
        self.eventcount   = 0
        AttrBase.__init__(self)

    def finalize(self, bestof, events):
        self.points.calc(bestof)
        self.missingrequired = [self._eventkey(e) for e in events if e.champrequire and self._eventkey(e) not in self.points.events]
        for e in events:
            if e.useastiebreak:
                self.tiebreakers.insert(0, self.points.get(self._eventkey(e)) or 0)
        self.tiebreakers.append(self.eventcount)

    def addResults(self, event, entry): 
        self.firstname = entry['firstname']
        self.lastname  = entry['lastname']
        self.driverid  = entry['driverid']
        idx = entry['position']-1
        if idx < len(self.tiebreakers) - 1:
            self.tiebreakers[idx] += 1
        self.eventcount += 1
        self.points.set(self._eventkey(event), entry['points'])

    def __repr__(self):
        return "%s %s: %s" % (self.firstname, self.lastname, self.points.total)

    def _eventkey(self, event):
        return "d-{}-id-{}".format(event.date, event.eventid)


class ChampClass(list):
    @property
    def entries(self):
        return sum([e['eventcount'] for e in self])

