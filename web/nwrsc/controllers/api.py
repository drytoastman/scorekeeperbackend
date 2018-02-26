"""
  This is the code for the JSON/XML results api.  Like the results interface, everything
  should be taken from the results table so that it continues to work after old series are
  expunged.
"""

import datetime
import itertools
import json
import logging
import uuid

from flask import request, g, escape, make_response

from nwrsc.controllers.blueprints import *
from nwrsc.lib.encoding import json_encode
from nwrsc.model import Result, Series
from nwrsc.api.models import *

log  = logging.getLogger(__name__)

from nwrsc.api.models.base_model_ import Model


def model2dict(model):
    dikt = {}
    for attr, _ in model.swagger_types.items():
        value = getattr(model, attr)
        if value is None:
            continue
        attr = model.attribute_map[attr]
        dikt[attr] = value
    return dikt


class SwaggerJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Model):
            return model2dict(o)
        if isinstance(o, datetime.datetime):
            return o.replace(microsecond=0).isoformat()+"Z"
        if isinstance(o, datetime.date):
            return o.isoformat()
        if isinstance(o, uuid.UUID):
            return str(o)
        return json.JSONEncoder.default(self, o)


class SwaggerXMLEncoder():
    """ XML in python doesn't have easy encoding or custom getter options like JSONEncoder so we do it ourselves. """
    def __init__(self):
        self.bits = list()

    def encode(self, data):
        self.toxml(data)
        return str(''.join(self.bits))

    def toxml(self, data):
        if isinstance(data, Model):           self._encodemodel(data)
        elif isinstance(data, (list, tuple)): self._encodelist(data)
        elif isinstance(data, (dict,)):       self._encodedict(data)
        else:                                 self._encodedata(data)

    def _encodelist(self, data):
        if all(isinstance(x, (int,float,str)) for x in data):
            self.bits.append("<rawlist>")
            for d in data:
                if isinstance(d, float): self.bits.append("<float>{}</int>".format(d))
                elif isinstance(d, int): self.bits.append("<int>{}</int>".format(d))
                elif isinstance(d, str): self.bits.append("<string>{}</string>".format(d))
            self.bits.append("</rawlist>")
        else:
            for v in data:
                self.toxml(v)

    def _encodedict(self, data):
        for k,v in sorted(data.items()):
            if len(k) > 0 and k[0] == '_': 
                continue
            self.bits.append('<%s>'  % k)
            self.toxml(v)
            self.bits.append('</%s>' % k)

    def _encodemodel(self, data):
        self.bits.append('<%s>'  % data.__class__.__name__)
        self._encodedict(model2dict(data))
        self.bits.append('</%s>' % data.__class__.__name__)

    def _encodedata(self, data):
        if isinstance(data, datetime.datetime):
            self.bits.append(data.replace(microsecond=0).isoformat()+"Z")
        elif isinstance(data, datetime.date):
            self.bits.append(data.isoformat())
        else:
            self.bits.append(escape(str(data)))


def api_encode(data):
    accepted = ['application/json', 'application/xml', 'text/xml']
    retformat = request.accept_mimetypes.best_match(accepted, 'text/html')
    retcode = "200"
    log.warning(retformat)

    if retformat.endswith('/json'):
        data = SwaggerJSONEncoder().encode(data)
    elif retformat.endswith('/xml'):
        data = SwaggerXMLEncoder().encode(data)
    else:
        data = "<html><h1>406 Not Acceptable</h1>This endpoint expects an <b>Accept</b> header with one of ({}) but the provided options were:" \
               "<br/><br/><pre>   {}</pre>".format(", ".join(["<b>{}</b>".format(x) for x in accepted]), request.accept_mimetypes)
        retcode = "406"

    response = make_response(data)
    response.headers['Content-type'] = retformat
    response.status = retcode
    return response


def format_classresults(code, data):
    """ takes class results for a single classcode and creates the swagger modeled version """
    from nwrsc.api.models.class_results import ClassResults
    from nwrsc.api.models.result_entry  import ResultEntry
    ret = ClassResults(classcode=code, entries=[])
    if data:
        for r in data:
            r['runs'] = itertools.chain.from_iterable(r['runs']) # Flatten 2D array into 1D
            ret.entries.append(ResultEntry.from_dict(r))
    return ret

def format_classchampresults(code, data):
    from nwrsc.api.models.class_champ_results import ClassChampResults
    from nwrsc.api.models.champ_entry import ChampEntry
    ret = ClassChampResults(classcode=code, entries=[])
    if data:
        for r in data:
            r['events'] = [{'eventdate':d1[2:], 'points':p1, 'drop':d1 in r['points']['drop']} for d1,p1 in r['points']['events'].items()]
            r['points'] = r['points']['total']
            ret.entries.append(ChampEntry.from_dict(r))
    return ret


def format_challengeresults(round, data):
    from nwrsc.api.models.challenge_round import ChallengeRound
    if data is None or round <= 0:
        return ChallengeRound()
    data['top']    = data['e1']
    data['bottom'] = data['e2']
    data['winner'] = { 1: 'top', 2: 'bottom' }.get(data['winner'], None)
    return ChallengeRound.from_dict(data)


@Api.route("/")
def serieslist():
    return api_encode(sorted(itertools.chain.from_iterable(Series.byYear().values())))

@Api.route("/<series>")
def seriesinfo():
    from nwrsc.api.models.series_info import SeriesInfo
    data = Result.getSeriesInfo()
    for e in data['events']:
        e['eventdate'] = e['date']  # fix up name, 'date' conflicts with date type in model definitions
    return api_encode(SeriesInfo.from_dict(data))

@Api.route("/<series>/event/<uuid:eventid>")
def eventresults():
    from nwrsc.api.models.event_results import EventResults
    return api_encode(EventResults(eventid=g.eventid, classes=[format_classresults(cls, results) for cls,results in Result.getEventResults(g.eventid).items()]))

@Api.route("/<series>/event/<uuid:eventid>/<classcode>")
def classresults(classcode):
    return api_encode(format_classresults(classcode, Result.getEventResults(g.eventid).get(classcode, None)))

@Api.route("/<series>/challenge/<uuid:challengeid>")
def challengeresults():
    from nwrsc.api.models.challenge_results import ChallengeResults
    return api_encode(ChallengeResults(challengeid=g.challengeid, rounds=[format_challengeresults(round,data) for round,data in Result.getChallengeResults(g.challengeid).items()]))

@Api.route("/<series>/challenge/<uuid:challengeid>/<int:round>")
def roundresults(round):
    from nwrsc.api.models.challenge_results import ChallengeResults
    data = Result.getChallengeResults(g.challengeid).get(round, None)
    return api_encode(format_challengeresults(round,data))

@Api.route("/<series>/champ")
def champresults():
    from nwrsc.api.models.champ_results import ChampResults
    return api_encode(ChampResults(series=g.series, classes=[format_classchampresults(code, results) for code, results in Result.getChampResults().items()]))

@Api.route("/<series>/champ/<classcode>")
def classchampresults(classcode):
    return api_encode(format_classchampresults(classcode, Result.getChampResults().get(classcode, None)))


@Api.route("/<series>/scca/<uuid:eventid>")
def scca():
    from nwrsc.api.models.entry import Entry
    results = Result.getEventResults(g.eventid)
    entries = list()
    for cls in results:
        for res in results[cls]:
            entries.append(Entry(first_name=res['firstname'],
                                 last_name=res['lastname'],
                                 member_no=res['membership'],
                                 _class=res['classcode'],
                                 index=res['indexcode'],
                                 pos=res['position'],
                                 car_model="%s %s %s %s" % (res.get('year',''), res.get('make',''), res.get('model',''), res.get('color','')),
                                 car_no="%s" % (res['number']),
                                 total_tm="%0.3lf" % res['net']
                            ))

    response = make_response("<Entries>" + SwaggerXMLEncoder().encode(entries) + "</Entries>")
    response.headers['Content-type'] = 'text/xml'
    return response
