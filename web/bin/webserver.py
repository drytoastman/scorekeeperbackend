#!/usr/local/bin/python

import gevent.monkey
gevent.monkey.patch_all()
import psycogreen.gevent
psycogreen.gevent.patch_psycopg()

import logging
import os
from gunicorn.app.wsgiapp import WSGIApplication
from sccommon.logging import logging_setup

class MyApp(WSGIApplication):
    def init(self, parser, opts, args):
        opts.worker_class = "geventwebsocket.gunicorn.workers.GeventWebSocketWorker"
        opts.bind = ["0.0.0.0:80"]
        opts.args=['nwrsc.app:create_app()']
        #opts.workers = 2
        opts.worker_tmp_dir="/dev/shm"
        opts.logconfig_dict = {
            "loggers" : { "gunicorn.error": { "propagate": True }},
            "root": {},
            "handlers": {},
            "formatters": {}
        }
        if os.environ.get('DEBUG', False):
            opts.timeout = 9000  # Don't kill worker while in pdb, but causes longer reload wait if syntax error
            opts.reload = True
        super().init(parser, opts, args=opts.args)

if __name__ == '__main__':
    logging_setup('/var/log/scweb.log')
    logging.getLogger('werkzeug').setLevel(logging.WARN)
    logging.getLogger('geventwebsocket.handler').setLevel(logging.WARNING)
    logging.getLogger("webserver").info("starting server")

    MyApp().run()
