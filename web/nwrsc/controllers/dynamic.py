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

def _boolarg(arg):
    try:
        return request.args.get(arg, '0') in ('1', 'true', 'yes')
    except:
        return False

@Announcer.route("/event/<uuid:eventid>/")
def index():
    g.event = Event.get(g.eventid)
    mini = _boolarg('mini')
    if mini:
        return render_template('/announcer/mini.html')
    else:
        return render_template('/announcer/main.html')

@Announcer.route("/event/<uuid:eventid>/next")
def nextresult():
    # use ceil so round off doesn't cause an infinite loop
    try:
        modified = math.ceil(float(request.args.get('modified', '0')))
        mini = _boolarg('mini')
    except Exception as e:
        abort(400, "Invalid parameter data: {}".format(e))

    # Long polling, hold the connection until something is actually new
    then  = time.time()
    moddt = datetime.datetime.fromtimestamp(modified)

    # Limit lookback to the date of the event
    event = Event.get(g.eventid)
    midnight = datetime.datetime.combine(event.date, datetime.time(0))
    if moddt < midnight:
        moddt = midnight

    while True:
        result = Run.getLast(g.eventid, moddt)
        if result: # Not an empty dict
            data = loadAnnouncerResults(result['last_entry']['carid'], mini)
            data['modified'] = result['last_entry']['modified'].timestamp()
            return json_encode(data)
        if time.time() > then + MAX_WAIT:  # wait max to stop forever threads
            return json_encode({})
        g.db.rollback()
        time.sleep(1.0)

@Announcer.route("/timer")
@Announcer.route("/event/<uuid:eventid>/timer")
def timer():
    # Long polling, hold the connection until the timer reports different data
    try:
        lasttimer = float(request.args.get('lasttimer', '0'))
    except Exception as e:
        abort(400, "Invalid parameter data: {}".format(e))

    then = time.time()
    while True:
        result = TimerTimes.getLast()
        if result and result != lasttimer:
            return json_encode({'timer': result})
        if time.time() > then + MAX_WAIT:  # wait max to stop forever threads
            return json_encode({})
        g.db.rollback()
        time.sleep(1.0)
 
def loadAnnouncerResults(carid, mini):
    settings  = Settings.getAll()
    classdata = ClassData.get()
    event     = Event.get(g.eventid)
    results   = Result.getEventResults(g.eventid)
    nextid    = RunOrder.getNextCarIdInOrder(carid, g.eventid)
    order     = list()
    if not mini:
        champ     = Result.getChampResults()
        tttable   = get_template_attribute('/results/ttmacros.html', 'toptimestable')

    def entrant_tables(cid):
        (group, driver) = Result.getDecoratedClassResults(settings, results, cid)
        if driver is None:
            return "No result data for carid {}".format(cid)
        if mini:
            decchamp = ""
        elif event.ispractice:
            decchamp = "practice event"
        elif classdata.classlist[driver['classcode']].champtrophy:
            decchamp = Result.getDecoratedChampResults(champ, driver)
        else:
            decchamp = "Not a champ class"
        return render_template('/announcer/entrant.html', event=event, driver=driver, group=group, champ=decchamp)

    for n in RunOrder.getNextRunOrder(carid, g.eventid):
        if n.classcode in results:
            for e in results[n.classcode]:
                if e['carid'] == str(n.carid):
                    order.append((e, Result.getBestNetRun(e)))
                    break

    data = {}
    data['last']   = entrant_tables(carid)
    data['order']  = render_template('/announcer/runorder.html', order=order)
    if not mini:
        data['next']   = entrant_tables(nextid)
        data['topnet'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':True, 'counted':False}, carid=carid))
        data['topraw'] = tttable(Result.getTopTimesTable(classdata, results, {'indexed':False, 'counted':False}, carid=carid))
        for ii in range(1, event.segments+1):
            ret['topseg%d'% ii] = toptimestable(Result.getTopTimesTable(classdata, results, {'seg':ii}, carid=carid))

    return data

