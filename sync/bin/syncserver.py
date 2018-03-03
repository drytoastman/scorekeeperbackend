#!/usr/bin/env python3

import datetime
import logging
import logging.handlers
import os
import pytz
import signal
import synclogic
import sys
import time
import threading


class DTFormatter(logging.Formatter):
    """ Class to use datetime rather than time_struct for formatting so we can including time zone """
    def formatTime(self, record, datefmt=None):
        # Have to reach into environ directly here as the app isnt necessarily created yet so we can read its config
        tz  = pytz.timezone(os.environ.get('UI_TIME_ZONE', 'US/Pacific'))
        return datetime.datetime.fromtimestamp(record.created).astimezone(tz).strftime(datefmt)


if __name__ == '__main__':
    level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'), logging.INFO)
    tz    = pytz.timezone(os.environ.get('UI_TIME_ZONE', 'US/Pacific'))

    fmt = DTFormatter('%(asctime)s %(name)s %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S %Z')
    root  = logging.getLogger()
    root.setLevel(level)
    root.handlers = []

    fhandler = logging.handlers.RotatingFileHandler('/var/log/scsync.log', maxBytes=10000000, backupCount=10)
    fhandler.setFormatter(fmt)
    fhandler.setLevel(level)
    root.addHandler(fhandler)

    if 'DEBUG' in os.environ:
        shandler = logging.StreamHandler()
        shandler.setFormatter(fmt)
        shandler.setLevel(level)
        root.addHandler(shandler)

    log = logging.getLogger(__name__)
    log.info("starting main")
    mp = synclogic.process.MergeProcess(sys.argv[1:])
    done = False

    def interrupt(signum, frame):
        log.info("Received signal {}".format(signum))
        global mp, done
        if signum == signal.SIGHUP:
            mp.poke()
        else:
            mp.shutdown()
            done = True

    signal.signal(signal.SIGABRT, interrupt)
    signal.signal(signal.SIGINT,  interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGHUP,  interrupt)

    t = threading.Thread(target=mp.runforever)
    t.start()
    while not done:
        time.sleep(1)
    log.info("exiting main")
