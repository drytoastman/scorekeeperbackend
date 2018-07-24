#!/usr/bin/env python3

from cheroot import wsgi
from cheroot.workers import threadpool
import logging
import nwrsc.app 
import os
import requests
import signal
import sys
import threading
import time

from sccommon.logging import logging_setup

server = None

def removepid(signum, frame):
    logging.getLogger("webserver").info("stopping server")
    global server
    if server:
        server.stop()
    os.remove(pidfile)
    sys.exit(0)

def patchinit(orig):
    def newinit(self, server):
        orig(self, server)
        self.daemon = True
    return newinit

def justdie(self, timeout=None):
    return

class CronThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        while True:
            time.sleep(3600) # Sleep an hour
            requests.get('http://localhost/admin/cron')

if __name__ == '__main__':
    pidfile = os.path.expanduser('~/nwrscwebserver.pid')
    signal.signal(signal.SIGABRT, removepid)
    signal.signal(signal.SIGINT,  removepid)
    signal.signal(signal.SIGTERM, removepid)
    with open(pidfile, 'w') as fp:
        fp.write(str(os.getpid()))

    cron = bool(os.environ.get('DOCRON', False))
    port = int(os.environ.get('PORT', 80))

    logging_setup('/var/log/scweb.log')
    logging.getLogger('werkzeug').setLevel(logging.WARN)
    theapp = nwrsc.app.create_app()
    nwrsc.app.model_setup(theapp)

    logging.getLogger("webserver").info("starting server")
    if cron:
       CronThread().start()

    threadpool.WorkerThread.__init__ = patchinit(threadpool.WorkerThread.__init__)
    threadpool.ThreadPool.stop = justdie 
    server = wsgi.Server(('0.0.0.0', port), theapp, numthreads=100, shutdown_timeout=1, server_name="Scorekeeper 2.3")
    server.start()

    removepid(0, 0) # just in case we get here somehow
