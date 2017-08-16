#!/usr/bin/env python

import http.server
import json
import logging
import threading
import traceback

log = logging.getLogger(__name__)

class JSONHandler(http.server.BaseHTTPRequestHandler):

    def log_request(self, code='-', size='-'):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        with self.server.wrappedstate as data:
            self.wfile.write(json.dumps(data).encode('UTF-8'))
        return

    def do_POST(self):
        try:
            self.server.dataqueue.put_nowait(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(traceback.format_exc().encode('UTF-8'))
        return self.do_GET()


class JSONServer(http.server.HTTPServer):

    def __init__(self, wrappedstate, dataqueue):
        http.server.HTTPServer.__init__(self, ("", 80), JSONHandler)
        self.wrappedstate = wrappedstate
        self.dataqueue = dataqueue


class FrontendThread(threading.Thread):

    def __init__(self, wrappedstate, dataqueue):
        threading.Thread.__init__(self)
        self.wrappedstate = wrappedstate
        self.dataqueue = dataqueue

    def run(self):
        log.info("starting http server")
        self.server = JSONServer(self.wrappedstate, self.dataqueue)
        self.server.serve_forever()
        log.info("exiting frontend")

    def stop(self):
        if self.server:
            self.server.shutdown()

