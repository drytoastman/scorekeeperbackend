"""
    Handlers for dynamically updated pages like the announcer page.  This will take
    a lot of results of the results table but is also free to the use other series
    tables as needed.  It will not function with offline series
"""
import collections
import datetime
import functools
import json
import logging
import math
import time
import types
import urllib
import uuid

from flask import abort, current_app, g, get_template_attribute, request, render_template

from nwrsc.controllers.blueprints import *
from nwrsc.lib.encoding import json_encode
from nwrsc.model import *
from nwrsc.lib.misc import ArchivedSeriesException, csvlist

log = logging.getLogger(__name__)

MAX_WAIT = 30

@Announcer.before_request
def activecheck():
    if g.seriestype != Series.ACTIVE:
        raise ArchivedSeriesException()

@Announcer.endpoint("Announcer.base")
@Announcer.route("/", endpoint='eventlist')
def serieslist():
    return render_template('announcer/bluebase.html')

def boolarg(arg):
    try: return request.args.get(arg, '0') in ('1', 'true', 'yes')
    except: return False

def tryint(arg):
    try: return int(arg)
    except: return arg

def tryfloat(arg):
    try: return float(arg)
    except: return arg

def floatoptarg(arg):
    try: return float(request.args.get(arg, None))
    except: return None

def modifiedarg(arg, limit):
    """
        Convert float string into a time limited datetime
        Uses ceil so round off doesn't cause an infinite loop
    """
    try:
        f = float(request.args.get(arg, None))
        moddt = datetime.datetime.fromtimestamp(math.ceil(f))
        if moddt < limit:
            moddt = limit
        return moddt
    except:
        return None

@Announcer.route("/event/<uuid:eventid>/")
def index():
    g.event = Event.get(g.eventid)
    mini = boolarg('mini')
    if mini:
        return render_template('/announcer/mini.html')
    elif g.event.ispro:
        return render_template('/announcer/pro.html')
    else:
        return render_template('/announcer/main.html')


bboard  = collections.defaultdict(set)
remotes = set()

def sockets_handler(config):
    log = logging.getLogger("nwrsc.SocketsHandler")
    while True:
        try:
            db   = AttrBase.connect(config['DBHOST'], config['DBPORT'], config['DBUSER'], app='wsserver')
            AttrBase.changelistener(config['DBHOST'], config['DBPORT'], config['DBUSER'], functools.partial(table_change, db))
        except Exception as e:
            log.warning("changelistener exception, will retry: {}".format(e))

        for rem in remotes:
            rem.close()
        bboard.clear()
        time.sleep(3)

def table_change(db, tablename):
    msg = None
    wsl = ()

    # Generate the new result
    if tablename == 'timertimes':
        lastrecord = TimerTimes.getLast(db)
        lastrecord = "1234.1231"
        if lastrecord: # and lastrecord != lasttimer:
            msg = json.dumps({'timer': lastrecord})
            wsl = bboard['timer']

    # Send to all those that requested it
    for ws in wsl:
        ws.send(msg)


@Announcer.route("/event/<uuid:eventid>/ws")
def announcerws():
    ws = request.environ.get('wsgi.websocket', None)
    if not ws:
        return "Expecting a websocket here"

    remotes.add(ws)
    try:
        while not ws.closed:
            # Only received messages are requests for what to send
            msg = json.loads(ws.receive())
            if 'request' in msg:
                for s in bboard.values():
                    s.discard(ws)
                for k,v in msg['request'].items():
                    bboard[k].add(ws)
    except Exception as e:
        log.warning(e)
    ws.close()
    return ""


@Announcer.route("/event/<uuid:eventid>/next")
def nextresult():
    event = Event.get(g.eventid)
    midnight = datetime.datetime.combine(event.date, datetime.time(0))
    try:
        lastclass    = modifiedarg('lastclass', midnight)
        lastresult   = modifiedarg('lastresult', midnight)
        lastprotimer = modifiedarg('lastprotimer', midnight)
        lasttimer  = floatoptarg('lasttimer')
        mini       = boolarg('mini')
        classcode  = request.args.get('classcode', '')
    except Exception as e:
        abort(400, "Invalid parameter data: {}".format(e))

    # Long polling, hold the connection until something is actually new
    then  = time.time()
    ret = {}
    while True:
        if lastresult is not None:
            lastrun = Run.getLast(g.eventid, lastresult)
            if lastrun: # Not an empty dict
                le = lastrun['last_entry']
                if g.event.ispro:
                    # Get the last run on the opposite course with the same classcode
                    back = lastresult - datetime.timedelta(seconds=60)
                    opp = Run.getLast(g.eventid, back, classcode=le['classcode'], course=le['course']=='1' and '2' or '1')
                    oppcarid = opp and opp['last_entry']['carid'] or None
                    data = loadProResults(le['carid'], int(le['course']), int(le['rungroup']), int(le['run']), oppcarid)
                else:
                    data = loadAnnouncerResults(le['carid'], int(le['course']), int(le['rungroup']), mini=mini)
                data['timestamp'] = le['modified'].timestamp()
                ret['lastresult'] = data

        if classcode and lastclass is not None:
            lastrun = Run.getLast(g.eventid, lastclass, classcode=classcode)
            if lastrun: # Not an empty dict
                data = loadClassResults(lastrun['last_entry']['carid'], int(lastrun['last_entry']['rungroup']))
                data['timestamp'] = lastrun['last_entry']['modified'].timestamp()
                ret['lastclass'] = data

        if lasttimer is not None:
            lastrecord = TimerTimes.getLast()
            if lastrecord and lastrecord != lasttimer:
                ret['lasttimer'] = lastrecord

        if lastprotimer is not None:
            events = EventStream.get(lastprotimer)
            if events:  # There are new events
                data = formatProTimer(events)
                data['timestamp'] = events[-1]['time'].timestamp()
                ret['lastprotimer'] = data

        if ret: # If we have data, return it now
            return json_encode(ret)

        if time.time() > then + MAX_WAIT: # wait max to stop forever threads
            return json_encode({})

        g.db.rollback() # Don't stay idle in transaction from SELECTs
        time.sleep(1.0)



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
    ret['left']  = render_template('/announcer/protimer.html', entries=record[0][-3:])
    ret['right'] = render_template('/announcer/protimer.html', entries=record[1][-3:])
    return ret


def entrantTables(store, settings, classdata, carid, results, champ, rungroup=None):
    (group, drivers) = Result.getDecoratedClassResults(settings, results, carid, rungroup=rungroup)
    if len(drivers):
        store['entrant'] = render_template('/announcer/entrant.html', event=g.event, driver=drivers[0])
        store['class']   = render_template('/announcer/class.html', event=g.event, classcode=drivers[0]['classcode'], group=group)
        if not champ:
            store['champ'] = ""
        elif g.event.ispractice:
            store['champ'] = ""
        elif classdata.classlist[drivers[0]['classcode']].champtrophy:
            store['champ'] = render_template('/announcer/champ.html', event=g.event, classcode=drivers[0]['classcode'], champ=Result.getDecoratedChampResults(champ, *drivers))
        else:
            store['champ'] = ""
    else:
        store['entrant'] = "No result data"
        store['class'] = "No result data"
        store['champ'] = "No result data"

    # We reuse the same data again, clear the current flag so that are decorations don't bleed
    for e in group:
        e.pop('current',None)


def loadClassResults(carid, rungroup):
    settings = Settings.getAll()
    classdata = ClassData.get()
    event    = Event.get(g.eventid)
    results  = Result.getEventResults(g.eventid)
    champ    = Result.getChampResults()
    ret      = {}
    entrantTables(ret, settings, classdata, carid, results, champ, rungroup=rungroup)

    return ret


def loadNextToFinish(nextcars, course, rungroup, results):
    order = list()
    for n in nextcars:
        key = n.classcode in results and n.classcode or str(rungroup)
        if key in results:
            for e in results[key]:
                if e['carid'] == str(n.carid):
                    order.append((e, Result.getBestNetRun(e, course=course)))
                    break
    return order


def loadAnnouncerResults(carid, course, rungroup, mini=False):
    settings  = Settings.getAll()
    classdata = ClassData.get()
    tttable   = get_template_attribute('/results/ttmacros.html', 'toptimestable')
    results   = Result.getEventResults(g.eventid)
    champ     = Result.getChampResults()

    data = {'current':{}, 'next':{}}
    nextorder = loadNextToFinish(RunOrder.getNextRunOrder(carid, g.eventid, course, rungroup), course, rungroup, results)

    entrantTables(data['current'], settings, classdata, carid, results, champ, rungroup=rungroup)
    data['order'] = render_template('/announcer/runorder.html', order=nextorder)
    if not mini:
        data['topnet'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':True,  'counted':False}, carid=carid))
        data['topraw'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':False, 'counted':False}, carid=carid))
        for ii in range(1, g.event.segments+1):
            data['topseg%d'% ii] = toptimestable(Result.getTopTimesTable(classdata, results, {'seg':ii}, carid=carid))
        nextid = nextorder and nextorder[0][0]['carid'] or None
        entrantTables(data['next'], settings, classdata, nextid, results, champ, rungroup=rungroup)

    return data


def loadProResults(carid, course, rungroup, run, opposite):
    settings  = Settings.getAll()
    classdata = ClassData.get()
    tttable   = get_template_attribute('/results/ttmacros.html', 'toptimestable')
    results   = Result.getEventResults(g.eventid)
    champ     = Result.getChampResults()
    side      = course == 1 and 'left' or 'right'

    nextorder = loadNextToFinish(RunOrder.getNextRunOrderPro(carid, g.eventid, course, rungroup, run), course, rungroup, results)

    data = {}
    data['topnet'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':True, 'counted':False}, carid=carid))
    data['topraw'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':False, 'counted':False}, carid=carid))
    for ii in range(1,3):
        data['topnet{}'.format(ii)] = tttable(Result.getTopTimesTable(classdata, results, {'course':ii, 'indexed':True }, carid=carid))
        data['topraw{}'.format(ii)] = tttable(Result.getTopTimesTable(classdata, results, {'course':ii, 'indexed':False, 'counted':False}, carid=carid))

    (classres,drivers) = Result.getDecoratedClassResults(settings, results, *filter(None, [carid, opposite]))
    champres           = Result.getDecoratedChampResults(champ, *drivers)
    data[side]    = render_template('/announcer/entrant.html', event=g.event, driver=drivers[0])
    data['class'] = render_template('/announcer/class.html',   event=g.event, classcode=drivers[0]['classcode'], group=classres)
    data['champ'] = render_template('/announcer/champ.html',   event=g.event, classcode=drivers[0]['classcode'], champ=champres)

    data[side+'nextfinish'] = render_template('/announcer/runorder.html', order=nextorder)

    return data
