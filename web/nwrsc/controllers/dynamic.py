"""
    Handlers for dynamically updated pages like the announcer page.  This will take
    a lot of results of the results table but is also free to the use other series
    tables as needed.  It will not function with offline series
"""
import datetime
import logging
import math
import time
import types
import urllib
import uuid

from flask import abort, current_app, g, get_template_attribute, request, render_template
from flask_assets import Bundle

from nwrsc.controllers.blueprints import *
from nwrsc.lib.encoding import json_encode
from nwrsc.model import *
from nwrsc.lib.misc import ArchivedSeriesException, csvlist

log = logging.getLogger(__name__)

MAX_WAIT = 30

@Announcer.before_app_first_request
def init():
    env = current_app.jinja_env.assets_environment
    env.register('announcer.js',      Bundle(env.j['jquery'], env.j['bootstrap'], "js/commonannouncer.js", "js/announcer.js", filters="rjsmin", output="announcer.js"))
    env.register('proannouncer.js',   Bundle(env.j['jquery'], env.j['bootstrap'], "js/commonannouncer.js", "js/proannouncer.js", filters="rjsmin", output="proannouncer.js"))
    env.register('announcer.css',     Bundle("scss/announcer.scss",     depends="scss/*.scss", filters="libsass", output="announcer.css"))
    env.register('announcermini.css', Bundle("scss/announcermini.scss", depends="scss/*.scss", filters="libsass", output="announcermini.css"))

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
                    opp = Run.getLast(g.eventid, lastresult, classcode=le['classcode'], course=le['course']=='1' and '2' or '1')
                    oppcarid = opp and opp['last_entry']['carid'] or None
                    data = loadProResults(le['carid'], le['course'], oppcarid)
                else:
                    data = loadAnnouncerResults(le['carid'], mini=mini)
                data['timestamp'] = le['modified'].timestamp()
                ret['lastresult'] = data

        if classcode and lastclass is not None:
            lastrun = Run.getLast(g.eventid, lastclass, classcode=classcode)
            if lastrun: # Not an empty dict
                data = loadClassResults(lastrun['last_entry']['carid'])
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


def entrantTables(store, settings, classdata, carid, results, champ):
    (group, driver) = Result.getDecoratedClassResults(settings, results, carid)
    if driver is None:
        store['entrant'] = "No result data for carid {}".format(carid)
    
    store['entrant'] = render_template('/announcer/entrant.html', event=g.event, driver=driver)
    store['class']   = render_template('/announcer/class.html', event=g.event, driver=driver, group=group)
    if not champ:
        store['champ'] = ""
    elif g.event.ispractice:
        store['champ'] = "practice event"
    elif classdata.classlist[driver['classcode']].champtrophy:
        store['champ'] = render_template('/announcer/champ.html', event=g.event, driver=driver, champ=Result.getDecoratedChampResults(champ, driver))
    else:
        store['champ'] = "Not a champ class"


def loadClassResults(carid):
    settings = Settings.getAll()
    classdata = ClassData.get()
    event    = Event.get(g.eventid)
    results  = Result.getEventResults(g.eventid)
    champ    = Result.getChampResults()
    ret      = {}
    entrantTables(ret, settings, classdata, event, carid, results, champ)
    return ret


def loadProResults(carid, course, opposite):
    settings  = Settings.getAll()
    classdata = ClassData.get()
    tttable   = get_template_attribute('/results/ttmacros.html', 'toptimestable')
    results   = Result.getEventResults(g.eventid)
    champ     = Result.getChampResults()

    data = {'left': {}, 'right': {}}
    data['topnet'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':True, 'counted':False}, carid=carid))
    data['topraw'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':False, 'counted':False}, carid=carid))
    for ii in range(1,3):
        data['topnet{}'.format(ii)] = tttable(Result.getTopTimesTable(classdata, results, {'course':ii, 'indexed':True }, carid=carid))
        data['topraw{}'.format(ii)] = tttable(Result.getTopTimesTable(classdata, results, {'course':ii, 'indexed':False, 'counted':False}, carid=carid))
    key1 = course == '1' and 'left' or 'right'
    key2 = key1 == 'left' and 'right' or 'left'
    entrantTables(data[key1], settings, classdata, carid, results, champ)
    entrantTables(data[key2], settings, classdata, opposite, results, champ)

    return data


def loadAnnouncerResults(carid, opposite=None, mini=False):
    settings  = Settings.getAll()
    classdata = ClassData.get()
    tttable   = get_template_attribute('/results/ttmacros.html', 'toptimestable')
    results   = Result.getEventResults(g.eventid)
    champ     = Result.getChampResults()

    data = {'current':{}, 'next':{}}
    order = list()
    for n in RunOrder.getNextRunOrder(carid, g.eventid):
        if n.classcode in results:
            for e in results[n.classcode]:
                if e['carid'] == str(n.carid):
                    order.append((e, Result.getBestNetRun(e)))
                    break

    entrantTables(data['current'], settings, classdata, carid, results, champ)
    data['order'] = render_template('/announcer/runorder.html', order=order)
    if not mini:
        data['topnet'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':True, 'counted':False}, carid=carid))
        data['topraw'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':False, 'counted':False}, carid=carid))
        for ii in range(1, g.event.segments+1):
            data['topseg%d'% ii] = toptimestable(Result.getTopTimesTable(classdata, results, {'seg':ii}, carid=carid))
        nextid = RunOrder.getNextCarIdInOrder(carid, g.eventid)
        entrantTables(data['next'], settings, classdata, nextid, results, champ)

    return data

