import datetime
from dateutil.parser import parse
from dateutil.tz import gettz
import glob
import logging
import logging.handlers
import os
import pytz

class DTFormatter(logging.Formatter):
    """ Class to use datetime rather than time_struct for formatting so we can including time zone """
    def formatTime(self, record, datefmt=None):
        tz  = pytz.timezone(os.environ.get('UI_TIME_ZONE', 'US/Pacific'))
        return datetime.datetime.fromtimestamp(record.created).astimezone(tz).strftime(datefmt)

def logging_setup(filename=None):
    level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'), logging.INFO)
    tz    = pytz.timezone(os.environ.get('UI_TIME_ZONE', 'US/Pacific'))
    debug = 'DEBUG' in os.environ

    fmt = DTFormatter('%(asctime)s %(name)s %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S %Z')
    root  = logging.getLogger()
    root.setLevel(level)
    root.handlers = []

    if filename:
        fhandler = logging.handlers.RotatingFileHandler(filename, maxBytes=10000000, backupCount=10)
        fhandler.setFormatter(fmt)
        fhandler.setLevel(level)
        root.addHandler(fhandler)

    if debug:
        shandler = logging.StreamHandler()
        shandler.setFormatter(fmt)
        shandler.setLevel(level)
        root.addHandler(shandler)


def collect_errors(fileglob='/var/log/sc*.log'):
    ret = {}
    for f in glob.glob(fileglob):
        ret[f] = collect_errors_file(f)
    return ret


def collect_errors_file(filename):
    collect = []
    add = False
    now = datetime.datetime.now(datetime.timezone.utc)
    limit = now - datetime.timedelta(days=1, hours=2)
    tzinfos = {'PDT': gettz("US/Pacific"), 'PST': gettz("US/Pacific")}

    with open(filename, 'r') as fp:
        for line in fp.readlines():
            bits = line.split()
            try:
                dt = parse(' '.join(bits[0:3]), tzinfos=tzinfos)
                if dt < limit:
                    add = False
                    continue

                if bits[4][:-1] in ('DEBUG', 'INFO', 'LOG'):
                    add = False
                else:
                    add = True
            except ValueError as ve: # traceback or other data
                pass
            except Exception as e: # traceback or other data
                collect.append("INTERNAL ERROR: " + str(e))

            if add:
                collect.append(line.strip())

    return collect
