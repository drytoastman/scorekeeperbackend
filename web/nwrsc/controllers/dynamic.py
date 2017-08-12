"""
    Handlers for dynamically updated pages like the announcer page.  This will take
    a lot of results of the results table but is also free to the use other series
    tables as needed.  It will not function with offline series
"""
import logging
import time
import urllib
import uuid
import math

from flask import Blueprint, abort, current_app, g, get_template_attribute, request, render_template
from nwrsc.lib.encoding import json_encode
from nwrsc.model import *
from nwrsc.lib.misc import csvlist

log = logging.getLogger(__name__)
Announcer = Blueprint("Announcer", __name__) 

MAX_WAIT = 30

# FINISH ME
# do we want 'if current_app.config['SHOWLIVE']' checks for announcer?
# Or just no link on the results page?

@Announcer.route("/")
def eventlist():
    return "event list here someday"


@Announcer.route("/event/<uuid:eventid>/")
def index():
    g.event = Event.get(g.eventid)
    mini = bool(request.args.get('mini', 0))
    if mini:
        return render_template('/announcer/mini.html')
    else:
        return render_template('/announcer/main.html')

@Announcer.route("/event/<uuid:eventid>/next")
def nextresult():
    # use ceil so round off doesn't cause an infinite loop
    modified = math.ceil(float(request.args.get('modified', '0')))
    mini = bool(request.args.get('mini', 0))

    # Long polling, hold the connection until something is actually new
    then = time.time()
    while True:
        result = Run.getLast(g.eventid, modified)
        if result != []:
            data = loadAnnouncerResults(result[0].carid, mini)
            data['modified'] = result[0].modified.timestamp()
            return json_encode(data)
        if time.time() > then + MAX_WAIT:  # wait max to stop forever threads
            return json_encode({})
        time.sleep(1.0)

@Announcer.route("/event/<uuid:eventid>/timer")
def timer():
    # Long polling, hold the connection until the timer reports different data
    lasttimer = request.args.get('lasttimer', '0')
    then = time.time()
    while True:
        result = Ephemeral.get('timer')
        if result and result != lasttimer:
            return json_encode({'timer': result})
        if time.time() > then + MAX_WAIT:  # wait max to stop forever threads
            return json_encode({})
        time.sleep(1.0)
 
def loadAnnouncerResults(carid, mini):
    settings  = Settings.get()
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
        elif classdata.classlist[driver['classcode']].champtrophy:
            decchamp = Result.getDecoratedChampResults(champ, driver)
        else:
            decchamp = "Not a champ class"
        return render_template('/announcer/entrant.html', event=event, driver=driver, group=group, champ=decchamp)

    for n in RunOrder.getNextRunOrder(carid, g.eventid):
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

# FINISH ME, to do later, not sure if this is even used....
class LiveController(object):

    def index(self):
        if self.eventid:
            return self._browser()
        elif self.database is not None:
            return self._events()
        else:
            return self._database()

    def _database(self):
        c.dblist = self._databaseList(archived=False)
        return render_mako('/live/database.mako')

    def _events(self):
        c.events = self.session.query(Event).all()
        return render_mako('/live/events.mako')

    def _browser(self):
        c.event = self.event
        c.classes = [x[0] for x in self.session.query(Class.code).all()]
        return render_mako('/live/browser.mako')

    def Event(self):
        carid = int(self.routingargs.get('other', 0))
        c.results = self._classlist(carid)
        return render_mako_def('/live/tables.mako', 'classlist')

    def Champ(self):
        carid = int(self.routingargs.get('other', 0))
        c.champ = self._champlist(carid)
        c.cls = self.cls
        return render_mako_def('/live/tables.mako', 'champlist')

    def PAX(self):
        carid = int(self.routingargs.get('other', 0))
        c.toptimes = self._loadTopTimes(carid, raw=False)
        return render_mako('/announcer/topnettimes.mako').replace('\n', '')

    def Raw(self):
        carid = int(self.routingargs.get('other', 0))
        c.toptimes = self._loadTopTimes(carid, raw=True)
        return render_mako('/announcer/toprawtimes.mako').replace('\n', '')
