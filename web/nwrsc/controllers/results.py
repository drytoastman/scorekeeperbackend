"""
  This is the code for the results pages. Everything should be taken from the results table so
  that it continues to work after old series are expunged.
"""
from operator import itemgetter
import logging
import re

from flask import Blueprint, request, render_template, get_template_attribute, make_response, g
from nwrsc.model import Audit, Entrant, Result, Registration, RunGroups, Series
from nwrsc.lib.bracket import Bracket
from nwrsc.lib.misc import ArchivedSeriesException, csvlist, InvalidChallengeException, InvalidEventException

Results = Blueprint("Results", __name__)
log = logging.getLogger(__name__)

## The indexes and lists

@Results.before_request
def setup():
    g.title = 'Scorekeeper Results'
    g.seriesyears = Series.byYear()
    if g.series:
        g.year = Series.getYear(g.series)
        g.seriesinfo = Result.getSeriesInfo()
        g.settings = g.seriesinfo.getSettings()
        g.events = g.seriesinfo.getEvents()
        if g.eventid:
            g.event = g.seriesinfo.getEvent(g.eventid)
            if g.event is None:
                raise InvalidEventException()
    elif len(g.seriesyears) == 1:
        g.year = next(iter(g.seriesyears))
    else:
        g.year = request.args.get('year', None)


@Results.endpoint("Results.base")
@Results.route("/")
def index():
    return render_template('results/bluebase.html')

@Results.route("/event/<uuid:eventid>/")
def event():
    if not g.seriesinfo.getEvent(g.eventid):
        raise InvalidEventException()
    results = Result.getEventResults(g.eventid)
    active  = results.keys()
    event   = g.seriesinfo.getEvent(g.eventid)
    challenges = g.seriesinfo.getChallengesForEvent(g.eventid)
    return render_template('results/eventindex.html', event=event, active=active, challenges=challenges, isactive=(g.seriestype==Series.ACTIVE))

## Basic results display

def _resultsforclasses(clslist=None, grplist=None):
    """ Show our class results """
    resultsbase = Result.getEventResults(g.eventid)
    g.classdata = g.seriesinfo.getClassData() 
    g.event     = g.seriesinfo.getEvent(g.eventid)

    if clslist is None and grplist is None:
        ispost         = True
        results        = resultsbase
        g.toptimes     = Result.getTopTimesTable(g.classdata, results, {'indexed':True}, {'indexed':False})
        g.entrantcount = sum([len(x) for x in results.values()])
    elif grplist is not None:
        ispost         = False
        results        = dict()
        for code, entries in resultsbase.items():
            for e in entries:
                if e['rungroup'] in grplist:
                    results[code] = entries
                    break
    else:
        ispost         = False
        results        = { k: resultsbase[k] for k in (set(clslist) & set(resultsbase.keys())) }

    return render_template('results/eventresults.html', ispost=ispost, results=results)


@Results.route("/event/<uuid:eventid>/byclass")
def byclass():
    classes = csvlist(request.args.get('list', ''))
    g.title = "Results For Class {}".format(','.join(classes))
    return _resultsforclasses(clslist=classes)

@Results.route("/event/<uuid:eventid>/bygroup")
def bygroup():
    groups = csvlist(request.args.get('list', ''), int)
    g.title = "Results For Group {}".format(','.join(map(str, groups)))
    return _resultsforclasses(grplist=groups)

@Results.route("/event/<uuid:eventid>/post")
def post():
    return _resultsforclasses()

@Results.route("/event/<uuid:eventid>/tt")
def tt():
    indexed  = bool(int(request.args.get('indexed', '1')))
    counted  = bool(int(request.args.get('counted', '1')))
    segments = bool(int(request.args.get('segments', '0')))
    course   = int(request.args.get('course', '0'))

    event     = g.seriesinfo.getEvent(g.eventid)
    classdata = g.seriesinfo.getClassData() 

    keys = []
    if segments:
        return "Implement the top segment times now. :)"
    elif course == 0 and event.courses > 1:
        keys.extend([{'indexed':indexed, 'counted':counted, 'course':c, 'title':c and "Course {}".format(c) or "Total"} for c in range(event.courses+1)])
    elif course == 0:
        keys.append({'indexed':True,  'counted':counted, 'course':0, 'title':'Top Index Times'})
        keys.append({'indexed':False, 'counted':counted, 'course':0, 'title':'Top Unindexed Times'})
    else:
        keys.append({'indexed':indexed, 'counted':counted, 'course':course, 'title':'Course {}'.format(course)})

    header   = "Top {} Times ({} Runs) for {}".format(indexed and "Indexed" or "", counted and "Counted" or "All", event.name)
    table    = Result.getTopTimesTable(classdata, Result.getEventResults(g.eventid), *keys)

    return render_template('/results/toptimes.html', header=header, table=table)

@Results.route("/champ/")
def champ():
    results = Result.getChampResults()
    events  = [x for x in g.events if not x.ispractice]
    return render_template('/results/champ.html', results=results, settings=g.settings, classdata=g.seriesinfo.getClassData(), events=events)


## ProSolo related data (Challenge and Dialins)

@Results.route("/event/<uuid:eventid>/dialins")
def dialins():
    orderkey = request.args.get('order', 'net')
    if orderkey not in ('net', 'prodiff'):
        return "Invalid order key"

    results = Result.getEventResults(g.eventid)
    entrants = [e for cls in results.values() for e in cls]
    entrants.sort(key=itemgetter(orderkey))
    return render_template('/challenge/dialins.html', orderkey=orderkey, event=g.event, entrants=entrants)

def _loadChallengeResults(challengeid, load=True):
    challenge = g.seriesinfo.getChallenge(challengeid)
    if challenge is None:
        raise InvalidChallengeException()
    return (challenge, load and Result.getChallengeResults(challengeid) or None)

@Results.route("/challenge/<uuid:challengeid>/bracket")
def bracket(challengeid):
    (challenge, results) = _loadChallengeResults(challengeid, load=False)
    (coords, size) = Bracket.coords(challenge.depth)
    return render_template('/challenge/bracketbase.html', challengeid=challengeid, coords=coords, size=size)

@Results.route("/challenge/<uuid:challengeid>/bracketimg")
def bracketimg(challengeid):
    (challenge, results) = _loadChallengeResults(challengeid)
    response = make_response(Bracket.image(challenge.depth, results))
    response.headers['Content-type'] = 'image/png'
    return response

@Results.route("/challenge/<uuid:challengeid>/bracketround/<int:round>")
def bracketround(challengeid, round):
    (challenge, results) = _loadChallengeResults(challengeid)
    roundReport = get_template_attribute('/challenge/challengemacros.html', 'roundReport')
    return roundReport(results[round])

@Results.route("/challenge/<uuid:challengeid>/")
def challenge(challengeid):
    (challenge, results) = _loadChallengeResults(challengeid)
    log.debug("{}, {}".format(challenge, results))
    return render_template('/challenge/challengereport.html', results=results, chal=challenge)

@Results.route("/event/<uuid:eventid>/audit")
def audit():
    if g.seriestype != Series.ACTIVE:
        raise ArchivedSeriesException()
    course = request.args.get('course', 1)
    group  = request.args.get('group', 1)
    order  = request.args.get('order', 'runorder')
    event  = g.event
    audit  = Audit.audit(event, course, group)

    if order in ['firstname', 'lastname']:
        audit.sort(key=lambda obj: str.lower(str(getattr(obj, order))))
    else:
        order = 'runorder'
        audit.sort(key=lambda obj: obj.row)

    return render_template('/results/audit.html', audit=audit, event=event, course=course, group=group, order=order)

@Results.route("/event/<uuid:eventid>/grid")
def grid():
    if g.seriestype != Series.ACTIVE:
        raise ArchivedSeriesException()
    order = request.args.get('order', 'number')
    groups = RunGroups.getForEvent(g.eventid)

    # Create a list of entrants in order of rungroup and [net/number]
    if order == 'position': 
        for l in Result.getEventResults(g.eventid).values():
            for d in l:
                groups.put(Entrant(**d))
    else: # number
        for e in Registration.getForEvent(g.eventid):
            groups.put(e)

    groups.sort(order)
    for go in groups.values():
        go.pad()
        go.number()

    return render_template('/results/grid.html', groups=groups, order=order, starts=[k for k in groups if k < 100])

