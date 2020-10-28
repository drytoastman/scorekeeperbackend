import csv
import datetime
import re
import json
import io
from flask import current_app, escape, make_response
import pytz
import types

def time_print(pgdt, fmt):
    """ Collect local time zone based printing in one place, expects one of our timezoneless UTC based times from postgres """
    tz = pytz.timezone(current_app.config['UI_TIME_ZONE'])
    return pgdt.astimezone(datetime.timezone.utc).astimezone(tz).strftime(fmt)


class JSONEncoderX(json.JSONEncoder):
    """ Helper for some special cases """
    def default(self, o):
        if hasattr(o, 'getAsDict'):
            return o.getAsDict()
        if isinstance(o, (set, types.GeneratorType)):
            return list(o)
        else:
            return str(o)

def to_json(obj):
    return JSONEncoderX().encode(obj)

def json_encode(data):
    response = make_response(to_json(data))
    response.headers['Content-type'] = 'application/json'
    return response

def ical_encode(data):
    response = make_response(ICalEncoder().encodeevents(data))
    response.headers['Content-type'] = 'text/calendar'
    return response

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


