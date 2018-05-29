"""
    Handlers for dynamically updated pages like the announcer page.  This will take
    a lot of results of the results table but is also free to the use other series
    tables as needed.  It will not function with offline series
"""
import datetime
import logging
import math
import time
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
    env.register('announcer.js',      Bundle(env.j['jquery'], env.j['bootstrap'], "js/announcer.js", filters="rjsmin", output="announcer.js"))
    env.register('announcer.css',     Bundle("scss/announcer.scss",     depends="scss/*.scss", filters="libsass", output="announcer.css"))
    env.register('announcermini.css', Bundle("scss/announcermini.scss", depends="scss/*.scss", filters="libsass", output="announcermini.css"))

@Announcer.endpoint("Announcer.base")
@Announcer.route("/", endpoint='eventlist')
def serieslist():
    return render_template('announcer/bluebase.html')

def boolarg(arg):
    try: return request.args.get(arg, '0') in ('1', 'true', 'yes')
    except: return False

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
        log.warning(g.event.ispro)
        return render_template('/announcer/pro.html')
    else:
        return render_template('/announcer/main.html')

@Announcer.route("/event/<uuid:eventid>/next")
def nextresult():
    event = Event.get(g.eventid)
    midnight = datetime.datetime.combine(event.date, datetime.time(0))
    try:
        lastclass  = modifiedarg('lastclass', midnight)
        lastresult = modifiedarg('lastresult',  midnight)
        lasttimer  = floatoptarg('lasttimer')
        mini       = boolarg('mini')
        classcode  = request.args.get('classcode', '')
    except Exception as e:
        abort(400, "Invalid parameter data: {}".format(e))

    # Long polling, hold the connection until something is actually new
    then  = time.time()
    ret = {}
    log.debug("starting loop with = {}".format(request.args))
    while True:
        if lastresult is not None:
            lastrun = Run.getLast(g.eventid, lastresult)
            if lastrun: # Not an empty dict
                data = loadAnnouncerResults(lastrun['last_entry']['carid'], mini)
                data['timestamp'] = lastrun['last_entry']['modified'].timestamp()
                ret['lastresult'] = data

        if classcode and lastclass is not None:
            lastrun = Run.getLast(g.eventid, lastclass, classcode)
            log.debug("{}, {}, {}".format(lastclass, classcode, lastrun))
            if lastrun: # Not an empty dict
                data = loadClassResults(lastrun['last_entry']['carid'])
                data['timestamp'] = lastrun['last_entry']['modified'].timestamp()
                ret['lastclass'] = data

        if lasttimer is not None:
            lastrecord = TimerTimes.getLast()
            if lastrecord and lastrecord != lasttimer:
                ret['lasttimer'] = lastrecord

        if ret: # If we have data, return it now
            return json_encode(ret)

        if time.time() > then + MAX_WAIT: # wait max to stop forever threads
            return json_encode({})

        g.db.rollback() # Don't stay idle in transaction from SELECTs
        time.sleep(1.0)


def entrantTables(store, settings, classdata, event, carid, results, champ):
    (group, driver) = Result.getDecoratedClassResults(settings, results, carid)
    if driver is None:
        store['entrant'] = "No result data for carid {}".format(carid)
    
    store['entrant'] = render_template('/announcer/entrant.html', event=event, driver=driver, group=group)
    store['class']   = render_template('/announcer/class.html', event=event, driver=driver, group=group)
    if not champ:
        store['champ'] = ""
    elif event.ispractice:
        store['champ'] = "practice event"
    elif classdata.classlist[driver['classcode']].champtrophy:
        store['champ'] = render_template('/announcer/champ.html', event=event, driver=driver, group=group, champ=Result.getDecoratedChampResults(champ, driver))
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


def loadAnnouncerResults(carid, mini):
    settings  = Settings.getAll()
    classdata = ClassData.get()
    event     = Event.get(g.eventid)
    results   = Result.getEventResults(g.eventid)
    nextid    = RunOrder.getNextCarIdInOrder(carid, g.eventid)
    order     = list()
    champ     = None
    if not mini:
        champ   = Result.getChampResults()
        tttable = get_template_attribute('/results/ttmacros.html', 'toptimestable')

    for n in RunOrder.getNextRunOrder(carid, g.eventid):
        if n.classcode in results:
            for e in results[n.classcode]:
                if e['carid'] == str(n.carid):
                    order.append((e, Result.getBestNetRun(e)))
                    break

    data = {}
    entrantTables(data, settings, classdata, event, carid, results, champ)
    data['order']  = render_template('/announcer/runorder.html', order=order)
    if not mini:
        data['next'] = {}
        entrantTables(data['next'], settings, classdata, event, nextid, results, champ)
        data['topnet'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':True, 'counted':False}, carid=carid))
        data['topraw'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':False, 'counted':False}, carid=carid))
        for ii in range(1, event.segments+1):
            data['topseg%d'% ii] = toptimestable(Result.getTopTimesTable(classdata, results, {'seg':ii}, carid=carid))

    return data

