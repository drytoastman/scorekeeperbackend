import datetime
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
    ret = []
    for f in glob.glob(fileglob):
        ret.append(f)
    return ret
