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

log = logging.getLogger(__name__)

## BulitenBoard
## [pgnotify][attrfrozenest] = set([websocket, ...])
bboard  = collections.defaultdict(lambda: collections.defaultdict(set))
remotes = set()

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


def table_change(app, db, payload):
    msg = None
    wsl = ()

    log.debug('change {}'.format(payload))

    watchers = bboard[payload]
    if not watchers:
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
            for ws in set.union(*watchers.values()): # ignore attr, nothing to use 
                ws.send(msg)

        elif table == 'localeventstream':
            pass

        elif table == 'runs':
            if not set.union(*watchers.values()): # no actual listeners
                return

            g.settings  = Settings.getAll()
            g.classdata = ClassData.get()
            g.resultscache = dict()
            g.champcache  = None
            g.nextordercache = None

            for attr, wslist in watchers.items():
                wslist = list(filter(lambda ws: not ws.closed, wslist))
                if not wslist: continue
                log.warning(wslist)

                res = nextResult(db, series, dict(attr), wslist[0].environ['LAST'][attr])
                if not res: continue

                msg = json.dumps(res[0])
                for ws in wslist:
                    try:
                        ws.send(msg)
                        ws.environ['LAST'][attr] = res[1]
                    except:
                        ws.close()
                    
                    


def lastTime(db, series):
    with db.cursor() as cur:
        try:
            cur.execute("set search_path='{}'".format(series))
            cur.execute("select raw from timertimes order by modified desc limit 1", ())
            value = cur.fetchone()[0]
            return json.dumps({'timer': value})
        except Exception as e:
            return None



def clean_bb(ws):
    # Clear any old watchers
    for attrdict in bboard.values():
        for wslist in attrdict.values():
            wslist.discard(ws)


def newWatchRequest(ws):
    clean_bb(ws)

    # Get our new stuff
    env = ws.environ['LIVE']
    watch = env.get('watch', {})
    series = env['series']

    if Series.type(series) != Series.ACTIVE:
        raise InvalidSeriesException()

    if 'timer' in watch:
        bboard[series+'.timertimes'][frozenset(watch['timer'].items())].add(ws)

    if 'protimer' in watch:
        bboard[series+'.localeventstream'][frozenset(watch['protimer'].items())].add(ws)

    if 'results' in watch:
        for attr in watch['results']:
            bboard[series+'.runs'][frozenset(attr.items())].add(ws)


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
    clean_bb(ws)
    remotes.discard(ws)
    return ""


def nextResult(db, series, attr, lastresult):
    event     = Event.get(attr['eventid'])
    classcode = attr.get('classcode', None)
    lastrun   = Run.getLast(event.eventid, lastresult, classcode=classcode)

    if lastrun: # Not an empty dict
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


def loadNextToFinish(nextcars, course, rungroup, results):
    order = list()
    for n in nextcars:
        key = n.classcode in results and n.classcode or str(rungroup)
        if key in results:
            for e in results[key]:
                if e['carid'] == str(n.carid):
                    order.append(e)
                    break
    return order


def loadEventResults(attr, event, carid, course, rungroup, run, **kwargs):

    if event.eventid not in g.resultscache:
        results = Result.getEventResults(event.eventid)
        for clscode, elist in results.items():
            for e in elist:
                try: e.pop('scca')
                except: pass
        (group, drivers) = Result.getDecoratedClassResults(g.settings, results, *filter(None, [carid, kwargs.get('oppcarid',None)]))
        g.resultscache[event.eventid] = (results, group, drivers)

    (results, group, drivers) = g.resultscache[event.eventid]
    if not drivers: return

    if attr.get('champ', False):
        if not g.champcache:
            champ = Result.getChampResults()
            cgroup = Result.getDecoratedChampResults(champ, *drivers)
            g.champcache = (champ, cgroup)
        (champ, cgroup) = g.champcache

    data = {}
    classcode = drivers[0]['classcode']

    if attr.get('entrant', False):
        data['entrant'] = drivers[0]

    if attr.get('class', False):
        data['class'] = { 'classcode':classcode, 'group':group }

    if attr.get('champ', False) and not event.ispractice and g.classdata.classlist[classcode].champtrophy:
        data['champ'] = { 'classcode':classcode, 'group':cgroup }

    if attr.get('topnet',      False): data['topnet']      = Result.getTopTimesTable(g.classdata, results, {'indexed':True,  'counted':True },              carid=carid)
    if attr.get('topnetleft',  False): data['topnetleft']  = Result.getTopTimesTable(g.classdata, results, {'indexed':True,  'counted':True,  'course': 1}, carid=carid)
    if attr.get('topnetright', False): data['topnetright'] = Result.getTopTimesTable(g.classdata, results, {'indexed':True,  'counted':True,  'course': 2}, carid=carid)

    if attr.get('topraw',      False): data['topraw']      = Result.getTopTimesTable(g.classdata, results, {'indexed':False, 'counted':False },             carid=carid)
    if attr.get('toprawleft',  False): data['toprawleft']  = Result.getTopTimesTable(g.classdata, results, {'indexed':False, 'counted':False, 'course': 1}, carid=carid)
    if attr.get('toprawright', False): data['toprawright'] = Result.getTopTimesTable(g.classdata, results, {'indexed':False, 'counted':False, 'course': 2}, carid=carid)

    # We reuse the same data again, clear the current flag so that are decorations don't bleed
    #for e in group:
    #    e.pop('current', None)

    if attr.get('next', False) or attr.get('runorder'):
        if not g.nextordercache:
            g.nextordercache = loadNextToFinish(RunOrder.getNextRunOrder(carid, event.eventid, course, rungroup), course, rungroup, results)

        if attr.get('runorder', False):
            data['runorder'] =  { 'course': course, 'run': run, 'next': g.nextordercache }

        if attr.get('next', False) and not event.ispro and g.nextordercache:
            data['next'] = {}
            nextid = g.nextordercache[0]['carid']
            (group, drivers) = Result.getDecoratedClassResults(g.settings, results, nextid, rungroup=rungroup)

            if attr.get('entrant', False):
                data['next']['entrant'] = drivers[0]

            if attr.get('class', False):
                data['next']['class'] = { 'classcode':classcode, 'group':group }

            if attr.get('champ', False) and not event.ispractice and g.classdata.classlist[classcode].champtrophy:
                cgroup = Result.getDecoratedChampResults(champ, *drivers)
                data['next']['champ'] = { 'classcode':classcode, 'group':cgroup }

    return data
