
import csv
import datetime
import re
import json
import icalendar
import io
from flask import current_app, escape, make_response
import pytz
import types

def time_print(pgdt, fmt):
    """ Collect local time zone based printing in one place, expects one of our timezoneless UTC based times from postgres """
    tz = pytz.timezone(current_app.config['UI_TIME_ZONE'])
    return pgdt.astimezone(datetime.timezone.utc).astimezone(tz).strftime(fmt)

def xml_encode(data, wrapper=None):
    response = make_response(XMLEncoder().encode(data, wrapper))
    response.headers['Content-type'] = 'text/xml'
    return response

def json_encode(data):
    response = make_response(JSONEncoder().encode(data))
    response.headers['Content-type'] = 'application/json'
    return response

def ical_encode(data):
    response = make_response(ICalEncoder().encodeevents(data))
    response.headers['Content-type'] = 'text/calendar'
    return response

def json_raw(data):
    response = make_response(data)
    response.headers['Content-type'] = 'application/json'
    return response

def to_json(obj):
    return JSONEncoder().encode(obj)

def csv_encode(filename, fields, data):
    buf = io.StringIO()
    csvw = csv.DictWriter(buf, fields, extrasaction='ignore')
    csvw.writeheader()
    csvw.writerows(data)
    response = make_response(buf.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename={}.csv".format(filename)
    response.headers["Content-Type"] = "text/csv"
    return response

class ICalEncoder():
    def encodeevents(self, data):
        cal = icalendar.Calendar()
        cal.add('prodid', '-//Scorekeeper Registration')
        cal.add('version', '2.0')
        cal.add('x-wr-calname;value=text', 'Scorekeeper Registration')
        cal.add('method', 'publish');
        for date, events in sorted(data.items()):
            for (series, name), reglist in sorted(events.items()):
                codes = [reg.classcode for reg in reglist]
                event = icalendar.Event()
                event.add('summary', "%s: %s" % (name, ','.join(codes)))
                event.add('dtstart', date)
                event['uid'] = 'SCOREKEEPER-CALENDAR-%s-%s' % (re.sub(r'\W','', name), date)
                cal.add_component(event)
        return cal.to_ical()


class JSONEncoder(json.JSONEncoder):
    """ Helper that calls getPublicFeed if available for getting json encoding """
    def default(self, o):
        if hasattr(o, 'getPublicFeed'):
            return o.getPublicFeed()
        elif isinstance(o, (set, types.GeneratorType)):
            return list(o)
        else:
            return str(o)


class XMLEncoder(object):
    """ XML in python doesn't have easy encoding or custom getter options like JSONEncoder so we do it ourselves. """
    def __init__(self):
        self.bits = list()

    def encode(self, data, wrapper=None):
        if wrapper:
            self.bits.append('<%s>' % wrapper)
        self.toxml(data)
        if wrapper:
            self.bits.append('</%s>' % wrapper)
        return str(''.join(self.bits))

    def toxml(self, data):
        if hasattr(data, 'getPublicFeed'):    self._encodefeed(data)
        elif isinstance(data, (list, tuple)): self._encodelist(data)
        elif isinstance(data, (dict,)):       self._encodedict(data)
        else:                                 self._encodedata(data)

    def _encodelist(self, data):
        if all(isinstance(x, (int,str)) for x in data):
            self.bits.append(escape(','.join(map(str, data))))
        else:
            for v in data:
                self.toxml(v)

    def _encodedict(self, data):
        tag = data.get('_type', None)
        if tag:
            self.bits.append('<%s>'  % tag)
        for k,v in sorted(data.items()):
            if len(k) > 0 and k[0] == '_': 
                continue
            self.bits.append('<%s>'  % k)
            self.toxml(v)
            self.bits.append('</%s>' % k)
        if tag:
            self.bits.append('</%s>'  % tag)

    def _encodefeed(self, data):
        self.bits.append('<%s>'  % data.__class__.__name__)
        self._encodedict(data.getPublicFeed())
        self.bits.append('</%s>' % data.__class__.__name__)

    def _encodedata(self, data):
        self.bits.append(escape(str(data)))

