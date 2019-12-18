#!/usr/local/bin/python

import gevent.monkey
gevent.monkey.patch_all()

import logging
from gunicorn.app.wsgiapp import WSGIApplication
from sccommon.logging import logging_setup

class MyApp(WSGIApplication):
    def init(self, parser, opts, args):
        opts.worker_class = "flask_sockets.worker"
        opts.bind = ["0.0.0.0:80"]
        opts.args=['nwrsc.app:create_app()']
        super().init(parser, opts, args=opts.args)

if __name__ == '__main__':
    logging_setup('/var/log/scweb.log')
    logging.getLogger('werkzeug').setLevel(logging.WARN)
    logging.getLogger('geventwebsocket.handler').setLevel(logging.INFO)
    logging.getLogger("webserver").info("starting server")

    MyApp().run()
