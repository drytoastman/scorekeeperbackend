"""
  This is the code for the results pages. Everything should be taken from the results table so
  that it continues to work after old series are expunged.
"""
import collections
import logging
from operator import itemgetter
import re
import uuid

from flask import request, render_template, get_template_attribute, make_response, g

from nwrsc.controllers.blueprints import *
from nwrsc.model import Audit, Entrant, Result, Registration, RunGroups, Series
from nwrsc.lib.misc import ArchivedSeriesException, csvlist, InvalidChallengeException, InvalidEventException

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
        log.debug(g.eventid)
        if g.eventid:
            g.event = g.seriesinfo.getEvent(g.eventid)
            if g.event is None:
                raise InvalidEventException()

        elif g.challengeid:
            g.challenge = g.seriesinfo.getChallenge(g.challengeid)
            if g.challenge is None:
                raise InvalidEventException()
            g.event = g.seriesinfo.getEvent(uuid.UUID(g.challenge.eventid))
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
    challenges = g.seriesinfo.getChallengesForEvent(g.eventid)
    return render_template('results/eventindex.html', event=g.event, active=active, challenges=challenges, isactive=(g.seriestype==Series.ACTIVE))

## Basic results display

def _resultsforclasses(clslist=None, grplist=None):
    """ Show our class results """
    resultsbase = Result.getEventResults(g.eventid)
    g.classdata = g.seriesinfo.getClassData() 

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

    return render_template('results/eventresults.html', event=g.event, ispost=ispost, results=results, disablemetascale=True)


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

@Results.route("/event/<uuid:eventid>/dist")
def dist():
    attr    = request.args.get('attr', 'net')
    results = Result.getEventResults(g.eventid)
    binnet  = collections.defaultdict(int)
    labels  = list()
    values  = list()
    for cls,res in results.items():
        for ent in res:
            if attr == 'net' and ent['indexval'] >= 1.000:
                continue
            if ent[attr] < 100:
                binnet[round(ent[attr]*2)/2] += 1

    idx = min(binnet.keys())
    end = max(binnet.keys())
    while idx <= end:
        labels.append(idx)
        values.append(binnet[idx])
        idx += 0.5

    title = {
        'net': 'PAX Distribution',
        'pen': 'Net Distribution'
    }[attr]

    return render_template("/results/chart.html", event=g.event, title=title, labels=labels, values=values)


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

    return render_template('/results/toptimes.html', event=g.event, header=header, table=table, disablemetascale=True)

@Results.route("/champ/")
def champ():
    results = Result.getChampResults()
    events  = [x for x in g.events if not x.ispractice]
    return render_template('/results/champ.html', event="x", results=results, settings=g.settings, classdata=g.seriesinfo.getClassData(), events=events, disablemetascale=True)


## ProSolo related data (Challenge and Dialins)

@Results.route("/event/<uuid:eventid>/dialins")
def dialins():
    orderkey = request.args.get('order', 'net')
    if orderkey not in ('net', 'prodiff'):
        return "Invalid order key"

    results = Result.getEventResults(g.eventid)
    entrants = [e for cls in results.values() for e in cls]
    entrants.sort(key=itemgetter(orderkey))
    return render_template('/challenge/dialins.html', orderkey=orderkey, event=g.event, entrants=entrants, disablemetascale=True)

def _loadChallengeResults(challengeid, load=True):
    challenge = g.seriesinfo.getChallenge(challengeid)
    if challenge is None:
        raise InvalidChallengeException()
    return (challenge, load and Result.getChallengeResults(challengeid) or None)


RANK1 =  [ 1 ]
RANK2 =  [ 2, 1 ]
RANK4 =  [ 3, 2, 4, 1 ]
RANK8 =  [ 6, 3, 7, 2, 5, 4, 8, 1 ]
RANK16 = [ 11, 6, 14, 3, 10, 7, 15, 2, 12, 5, 13, 4, 9, 8, 16, 1 ]
RANK32 = [ 22, 11, 27, 6, 19, 14, 30, 3, 23, 10, 26, 7, 18, 15, 31, 2, 21, 12, 28, 5, 20, 13, 29, 4, 24, 9, 25, 8, 17, 16, 32, 1 ]
RANKS = RANK32 + RANK16 + RANK8 + RANK4 + RANK2 + RANK1 + [0]
RANKS.reverse()

@Results.route("/challenge/<uuid:challengeid>/bracket")
def bracket():
    (challenge, results) = _loadChallengeResults(g.challengeid)
    challenge.baserounds = int(2**(challenge.depth-1))
    return render_template('/challenge/bracket.html', event=g.event, challenge=challenge, results=results, ranks=RANKS, disablemetascale=True)

@Results.route("/challenge/<uuid:challengeid>/bracketround/<int:round>")
def bracketround(round):
    (challenge, results) = _loadChallengeResults(g.challengeid)
    return render_template('/challenge/roundreport.html', round=results[round])

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
        for e in Registration.getForEvent(g.eventid, g.event.paymentRequired()):
            groups.put(e)

    groups.sort(order)
    for go in groups.values():
        go.pad()
        go.number()

    return render_template('/results/grid.html', groups=groups, order=order, starts=[k for k in groups if k < 100])

