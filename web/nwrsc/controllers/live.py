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

from flask import current_app, g, request

from nwrsc.model import *
from nwrsc.lib.misc import t3

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

    def event(self, eventid, *carids, rungroup=None):
        key = ('e', str(eventid), *map(str, carids), rungroup)
        if key not in self._calculated:
            self._calculated[key] = Result.getDecoratedClassResults(self.settings, self.eresults(eventid), *carids, rungroup=rungroup)
        return self._calculated[key]

    def champ(self, *drivers):
        key = ('c', *[str(d['driverid']) for d in drivers])
        if key not in self._calculated:
            self._calculated[key] = Result.getDecoratedChampResults(self.cresults, *drivers)
        return self._calculated[key]

    def nextorder(self, eventid, course, rungroup, carid):
        """ Get next carids in order and then match/return their results entries """
        key = ('n', str(eventid), course, rungroup, str(carid))
        if key not in self._calculated:
            nextcars = RunOrder.getNextRunOrder(carid, eventid, course, rungroup)
            order    = list()
            results  = self.eresults(eventid)
            for n in nextcars:
                subkey = n.classcode in results and n.classcode or str(rungroup)
                if subkey in results:
                    for e in results[subkey]:
                        if e['carid'] == str(n.carid):
                            order.append(e)
                            break
            self._calculated[key] = order
        return self._calculated[key]



def table_change(app, db, payload):
    msg = None
    wsl = ()

    log.debug('change {}'.format(payload))

    wslist = bboard[payload]
    wslist = list(filter(lambda ws: not ws.closed, wslist))
    if not wslist:
        return

    (series, table) = payload.split('.')

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
                for attr in ws.environ['LIVE']['watch']['results']:
                    try:
                        lastkey = frozenset(attr.items())
                        (res, ts) = nextResult(db, series, attr, ws.environ['LAST'][lastkey])
                        if not res: continue
                        msg = json.dumps(res)  # TODO: maybe get this cached as well
                        ws.send(msg)
                        ws.environ['LAST'][lastkey] = ts
                    except Exception as e:
                        log.warning(e)
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

    group, drivers = g.data.event(event.eventid, *filter(None, [carid, kwargs.get('oppcarid',None)]))
    if not drivers: return
    cgroup = g.data.champ(*drivers)

    data = {}
    classcode = drivers[0]['classcode']

    if attr.get('entrant', False):
        data['entrant'] = drivers[0]

    if attr.get('class', False):
        data['class'] = { 'classcode':classcode, 'order':group }

    if attr.get('champ', False) and not event.ispractice and g.data.classdata.classlist[classcode].champtrophy:
        data['champ'] = { 'classcode':classcode, 'order':cgroup }

    if attr.get('topnet',      False): data['topnet']      = Result.getTopTimesTable(g.data.classdata, results, {'indexed':True,  'counted':True },              carid=carid)
    if attr.get('topnetleft',  False): data['topnetleft']  = Result.getTopTimesTable(g.data.classdata, results, {'indexed':True,  'counted':True,  'course': 1}, carid=carid)
    if attr.get('topnetright', False): data['topnetright'] = Result.getTopTimesTable(g.data.classdata, results, {'indexed':True,  'counted':True,  'course': 2}, carid=carid)

    if attr.get('topraw',      False): data['topraw']      = Result.getTopTimesTable(g.data.classdata, results, {'indexed':False, 'counted':False },             carid=carid)
    if attr.get('toprawleft',  False): data['toprawleft']  = Result.getTopTimesTable(g.data.classdata, results, {'indexed':False, 'counted':False, 'course': 1}, carid=carid)
    if attr.get('toprawright', False): data['toprawright'] = Result.getTopTimesTable(g.data.classdata, results, {'indexed':False, 'counted':False, 'course': 2}, carid=carid)

    if attr.get('next', False) or attr.get('runorder'):
        if attr.get('runorder', False):
            data['runorder'] =  { 'course': course, 'run': run, 'next': g.data.nextorder(event.eventid, course, rungroup, carid) }

        if attr.get('next', False) and not event.ispro:
            data['next'] = {}
            nextids = g.data.nextorder(event.eventid, course, rungroup, carid)
            if nextids:
                (group, drivers) = g.data.event(event.eventid, nextids[0]['carid'], rungroup=rungroup)

                if attr.get('entrant', False):
                    data['next']['entrant'] = drivers[0]

                if attr.get('class', False):
                    data['next']['class'] = { 'classcode':classcode, 'order':group }

                if attr.get('champ', False) and not event.ispractice and g.data.classdata.classlist[classcode].champtrophy:
                    data['next']['champ'] = { 'classcode':classcode, 'order': g.data.champ(*drivers) }

    return data


## Below happens on websocket green thread

def newWatchRequest(ws):
    for wslist in bboard.values():
        wslist.discard(ws)

    # Get our new stuff
    env = ws.environ['LIVE']
    watch = env.get('watch', {})
    series = env['series']

    if Series.type(series) != Series.ACTIVE:
        raise InvalidSeriesException()

    if 'timer' in watch:
        bboard[series+'.timertimes'].add(ws)
        table_change(current_app, g.db, series+'.timertimes')

    if 'protimer' in watch:
        bboard[series+'.localeventstream'].add(ws)
        table_change(current_app, g.db, series+'.localeventstream')

    if 'results' in watch:
        bboard[series+'.runs'].add(ws)
        table_change(current_app, g.db, series+'.runs')


def live_websocket():
    ws = request.environ.get('wsgi.websocket', None)
    if not ws:
        return "Expecting a websocket here"

    try:
        remotes.add(ws)
        while not ws.closed: # Only receive messages are requests for what to send
            data = ws.receive()
            if data:
                ws.environ['LIVE'] = json.loads(data)
                ws.environ['LAST'] = collections.defaultdict(lambda: datetime.datetime.fromtimestamp(0))
                newWatchRequest(ws)
    except Exception as e:
        log.warning(e, exc_info=e)

    ws.close()
    for wslist in bboard.values():
        wslist.discard(ws)
    remotes.discard(ws)
    return ""

