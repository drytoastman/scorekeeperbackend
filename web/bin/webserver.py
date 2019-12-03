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

if __name__ == '__main__':
    pidfile = os.path.expanduser('~/nwrscwebserver.pid')
    signal.signal(signal.SIGABRT, removepid)
    signal.signal(signal.SIGINT,  removepid)
    signal.signal(signal.SIGTERM, removepid)
    with open(pidfile, 'w') as fp:
        fp.write(str(os.getpid()))

    logging_setup('/var/log/scweb.log')
    logging.getLogger('werkzeug').setLevel(logging.WARN)
    theapp = nwrsc.app.create_app()
    nwrsc.app.model_setup(theapp)

    logging.getLogger("webserver").info("starting server")

    threadpool.WorkerThread.__init__ = patchinit(threadpool.WorkerThread.__init__)
    threadpool.ThreadPool.stop = justdie 
    server = wsgi.Server(('0.0.0.0', int(os.environ.get('PORT', 80))), theapp, numthreads=100, shutdown_timeout=1, server_name="Scorekeeper 4.2")
    server.start()

    removepid(0, 0) # just in case we get here somehow
