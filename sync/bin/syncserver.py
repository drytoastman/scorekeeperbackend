#!/usr/bin/env python3

import logging
import logging.handlers
import os
import signal
import synclogic

if __name__ == '__main__':
    level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'), logging.INFO)
    fmt   = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')
    root  = logging.getLogger()
    root.setLevel(level)
    root.handlers = []

    fhandler = logging.handlers.RotatingFileHandler('/var/log/scsync.log', maxBytes=1000000, backupCount=10)
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
    mp = synclogic.process.MergeProcess()
    def interrupt(signum, frame):
        log.info("Received signal {}".format(signum))
        global mp
        if signum == signal.SIGHUP:
            mp.poke()
        else:
            mp.shutdown()

    signal.signal(signal.SIGABRT, interrupt)
    signal.signal(signal.SIGINT,  interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGHUP,  interrupt)

    mp.runforever()
    log.info("exiting main")
