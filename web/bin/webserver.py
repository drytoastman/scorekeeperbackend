#!/usr/bin/env python3

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
import logging
import nwrsc.app 
import os
import requests
import signal
import sys
import threading
import time

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

    level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'), logging.INFO)
    debug = bool(os.environ.get('DEBUG', False))
    cron  = bool(os.environ.get('DOCRON', False))
    port  = int(os.environ.get('PORT', 80))

    nwrsc.app.logging_setup(level=level, debug=debug)
    theapp = nwrsc.app.create_app()
    nwrsc.app.model_setup(theapp)

    logging.getLogger("webserver").info("starting server")
    if cron:
       CronThread().start()

    server = pywsgi.WSGIServer(('', port), theapp, handler_class=WebSocketHandler)
    server.serve_forever()

    removepid(0, 0) # just in case we get here somehow
