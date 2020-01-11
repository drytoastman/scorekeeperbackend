"""
    Websocket data feed for live updates
"""
import collections
import datetime
import functools
import json
import logging
import time
import uuid

from flask import current_app, g, render_template, request

from nwrsc.controllers.blueprints import *
from nwrsc.model import *
from nwrsc.lib.misc import ArchivedSeriesException, InvalidSeriesException, t3

log = logging.getLogger(__name__)

## BulitenBoard
## [pgnotify] = set([websocket, ...])
bboard  = collections.defaultdict(set)
remotes = set()

## Below happens on our single background green thread

def live_background_thread(app):
    log = logging.getLogger("nwrsc.SocketsHandler")
    while True:
        try:
            db = AttrBase.connect(app.config['DBHOST'], app.config['DBPORT'], app.config['DBUSER'], app='wsserver', autocommit=True) # don't leave SELECT idle-in-transactions
            AttrBase.changelistener(app.config['DBHOST'], app.config['DBPORT'], app.config['DBUSER'], functools.partial(table_change, app, db))
        except Exception as e:
            log.warning("changelistener exception, will retry: {}".format(e), exc_info=e)

        for rem in remotes:
            rem.close()
        bboard.clear()
        time.sleep(3)


class LazyData:

    def __init__(self):
        self._settings  = None
        self._classdata = None
        self._eresults  = dict()
        self._cresults  = None
        ###
        self._calculated = dict()

    @property
    def settings(self):
        if not self._settings: self._settings  = Settings.getAll()
        return self._settings

    @property
    def classdata(self):
        if not self._classdata: self._classdata = ClassData.get()
        return self._classdata

    def eresults(self, eventid):
        if eventid not in self._eresults:
            # load and filter results
            results = Result.getEventResults(eventid)
            for clscode, elist in results.items():
                for e in elist:
                    try: e.pop('scca')
                    except: pass
            self._eresults[eventid] = results
        return self._eresults[eventid]

    @property
    def cresults(self):
        if not self._cresults:
            self._cresults = Result.getChampResults()
        return self._cresults

    def event(self, eventid, carids, rungroup=None):
        key = ('e', str(eventid), *map(str, carids), rungroup)
        if key not in self._calculated:
            self._calculated[key] = Result.getDecoratedClassResults(self.settings, self.eresults(eventid), *carids, rungroup=rungroup)
        return self._calculated[key]

    def champ(self, *drivers):
        key = ('c', *[str(d['driverid']) for d in drivers])
        if key not in self._calculated:
            self._calculated[key] = Result.getDecoratedChampResults(self.cresults, *drivers)
        return self._calculated[key]

    def nextorder(self, eventid, course, rungroup, carid, classcode=None):
        """ Get next carids in order and then match/return their results entries """
        key = ('n', str(eventid), course, rungroup, str(carid))
        if key not in self._calculated:
            nextcars = RunOrder.getNextRunOrder(carid, eventid, course, rungroup, classcode=classcode)
            order    = list()
            results  = self.eresults(eventid)
            for n in nextcars:
                subkey = n.classcode in results and n.classcode or str(rungroup)
                if subkey in results:
                    for e in results[subkey]:
                        if e['carid'] == str(n.carid):
                            e['bestrun'] = Result.getBestNetRun(e, course=course)
                            order.append(e)
                            break
            self._calculated[key] = order
        return self._calculated[key]



def table_change(app, db, payload):
    # For now, we keep the old notifications on table only (no series) until we can update schemas
    msg = None
    wsl = ()

    log.debug('change {}'.format(payload))
    for k in bboard:
        if k[1] == payload:  # same table, check all series
            table_change_inner(app, db, k[0], k[1])


def table_change_inner(app, db, series, table):

    wslist = bboard[(series, table)]
    wslist = list(filter(lambda ws: not ws.closed, wslist))
    if not wslist:
        return

    with app.app_context():  # Need app context/g for model calls
        g.db = db
        g.series = series
        g.seriestype = Series.ACTIVE
        with g.db.cursor() as cur:
            cur.execute("SET search_path=%s,'public'", (g.series,))

        # Generate the new result
        if table == 'timertimes':
            value = TimerTimes.getLast()
            if not value: return
            msg = json.dumps({'timer': value})
            for ws in wslist:
                ws.send(msg)

        elif table == 'localeventstream':
            pass

        elif table == 'runs':
            g.data = LazyData()
            for ws in wslist:
                # Relay on LazyData caching to keep this efficient but not hard to follow
                attr = ws.environ['WATCH']
                try:
                    log.warning("check {} {}".format(ws, ws.environ['LAST']))
                    (res, ts) = nextResult(db, series, attr, ws.environ['LAST'])
                    if not res: continue
                    msg = json.dumps(res)  # TODO: maybe get this cached as well
                    ws.send(msg)
                    ws.environ['LAST'] = ts
                except Exception as e:
                    log.warning(e, exc_info=e)
                    ws.close()


def nextResult(db, series, attr, lastresult):
    event     = Event.get(attr['eventid'])
    classcode = attr.get('classcode', None)
    lastrun   = Run.getLast(event.eventid, lastresult, classcode=classcode)

    if not lastrun: # empty dict
        return (None, lastresult)

    le = lastrun['last_entry']
    args = dict(attr=attr, event=event, carid=le['carid'], course=int(le['course']), rungroup=int(le['rungroup']), run=int(le['run']))

    if event.ispro:
        # Get the last run on the opposite course with the same classcode
        back         = lastresult - datetime.timedelta(seconds=60)
        opp          = Run.getLast(event.eventid, back, classcode=le['classcode'], course=args['course']=='1' and '2' or '1')
        oppcarid     = opp and opp['last_entry']['carid'] or None
        data         = loadEventResults(oppcarid=oppcarid, **args)
        data['side'] = args['course'] == 1 and 'left' or 'right'
    else:
        data = loadEventResults(**args)

    data['timestamp'] = le['modified'].timestamp()
    return (data, le['modified'])



def lastTime(db, series):
    with db.cursor() as cur:
        try:
            cur.execute("set search_path='{}'".format(series))
            cur.execute("select raw from timertimes order by modified desc limit 1", ())
            value = cur.fetchone()[0]
            return json.dumps({'timer': value})
        except Exception as e:
            return None


def formatProTimer(events):
    record = [], []
    for e in events:
        etype = e['etype']
        if etype == 'TREE':
            record[0].append(dict())
            record[1].append(dict())

        elif etype == 'RUN':
            data     = e['event']['data']
            attr     = data['attr']
            course   = data['course']-1
            reaction = attr.get('reaction', '')
            sixty    = attr.get('sixty', '')
            status   = data.get('status', '')
            raw      = data.get('raw', 'NaN')
            if raw != 'NaN':  # run data
                for r in record[course]:
                    if r['reaction'] == reaction and r['sixty'] == sixty:
                        r['raw'] = raw
            elif len(record[course]):
                last = record[course][-1]
                last['reaction'] = reaction
                last['sixty']    = sixty
                last['status']   = status

    ret = {}
    ret['left']  = record[0][-3:]
    ret['right'] = record[1][-3:]
    return ret


def loadEventResults(attr, event, carid, course, rungroup, run, **kwargs):
    data         = {}
    eid          = event.eventid
    carids       = list(filter(None, [carid, kwargs.get('oppcarid', None)]))
    data['last'] = loadEntrantResults(attr, event=event, carids=carids, rungroup=rungroup)

    if attr.get('topnet',      False): data['topnet']      = Result.getTopTimesLists(g.data.classdata, g.data.eresults(eid), {'indexed':True,  'counted':True },              carid=carid).serial(0)
    if attr.get('topnetleft',  False): data['topnetleft']  = Result.getTopTimesLists(g.data.classdata, g.data.eresults(eid), {'indexed':True,  'counted':True,  'course': 1}, carid=carid).serial(0)
    if attr.get('topnetright', False): data['topnetright'] = Result.getTopTimesLists(g.data.classdata, g.data.eresults(eid), {'indexed':True,  'counted':True,  'course': 2}, carid=carid).serial(0)

    if attr.get('topraw',      False): data['topraw']      = Result.getTopTimesLists(g.data.classdata, g.data.eresults(eid), {'indexed':False, 'counted':False },             carid=carid).serial(0)
    if attr.get('toprawleft',  False): data['toprawleft']  = Result.getTopTimesLists(g.data.classdata, g.data.eresults(eid), {'indexed':False, 'counted':False, 'course': 1}, carid=carid).serial(0)
    if attr.get('toprawright', False): data['toprawright'] = Result.getTopTimesLists(g.data.classdata, g.data.eresults(eid), {'indexed':False, 'counted':False, 'course': 2}, carid=carid).serial(0)

    if attr.get('runorder', False):
        data['runorder'] =  { 'course': course, 'run': run, 'next': g.data.nextorder(eid, course, rungroup, carid) }

    if attr.get('next', False):
        nextids = g.data.nextorder(eid, course, rungroup, carid, classcode=attr.get('classcode', None))
        if nextids:
            data['next'] = loadEntrantResults(attr, event=event, carids=[nextids[0]['carid']], rungroup=rungroup)

    return data


def loadEntrantResults(attr, event, carids, rungroup):
    ret = {}
    if not carids:
        return ret

    (group, drivers) = g.data.event(event.eventid, carids, rungroup=rungroup)
    if not drivers:
        return ret

    classcode = drivers[0]['classcode']

    if attr.get('entrant', False):
        ret['entrant'] = drivers[0]

    if attr.get('class', False):
        ret['class'] = { 'classcode':classcode, 'order': group }

    if attr.get('champ', False) and not event.ispractice and g.data.classdata.classlist[classcode].champtrophy:
        ret['champ'] = { 'classcode':classcode, 'order': g.data.champ(*drivers) }

    return ret


## Below happens on websocket green thread

def new_watch_request(ws, req):
    for wslist in bboard.values():
        wslist.discard(ws)

    # Get our new stuff
    watch  = req.get('watch', {})
    ws.environ['WATCH'] = watch
    ws.environ['LAST']  = datetime.datetime.fromtimestamp(0)
    series = watch['series']

    if Series.type(series) != Series.ACTIVE:
        raise InvalidSeriesException()

    if 'timer' in watch:
        bboard[(series, 'timertimes')].add(ws)
        table_change_inner(current_app, g.db, series, 'timertimes')

    if 'protimer' in watch:
        bboard[(series, 'localeventstream')].add(ws)
        table_change_inner(current_app, g.db, series, 'localeventstream')

    if watch.keys() & set(['entrant', 'class', 'champ', 'next', 'topnet', 'topraw', 'runorder']):
        bboard[(series, 'runs')].add(ws)
        table_change_inner(current_app, g.db, series, 'runs')


@Live.route("/websocket")
def websocket():
    ws = request.environ.get('wsgi.websocket', None)
    if not ws:
        return "Expecting a websocket here"

    try:
        remotes.add(ws)
        while not ws.closed: # Only receive messages are requests for what to send
            data = ws.receive()
            if data:
                req = json.loads(data)
                if 'watch' in req:
                    new_watch_request(ws, req)

    except Exception as e:
        log.warning(e, exc_info=e)

    ws.close()
    for wslist in bboard.values():
        wslist.discard(ws)
    remotes.discard(ws)
    return ""


def event_check():
    g.seriestype = Series.type(g.series)
    if g.seriestype == Series.INVALID:
        raise InvalidSeriesException()
    if g.seriestype != Series.ACTIVE:
        raise ArchivedSeriesException()
    g.event = Event.get(g.eventid)
    g.classlist = []
    if not g.event.usingSessions():
        g.classlist = list(ClassData.get().classlist.keys())


@Live.route("/<series>/event/<uuid:eventid>/user")
def user():
    event_check()
    return render_template('live/panel.html', panel_type="user-panel")

@Live.route("/<series>/event/<uuid:eventid>/announcer")
def announcer():
    event_check()
    return render_template('live/panel.html', panel_type="announcer-panel")

