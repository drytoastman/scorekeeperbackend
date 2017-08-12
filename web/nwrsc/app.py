import sys
import os
import datetime
import logging
import threading
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from operator import attrgetter

import psycopg2 
from flask import Flask, request, abort, g, current_app, render_template, send_from_directory
from flask_compress import Compress
from flask_assets import Environment, Bundle
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer
from werkzeug.debug.tbtools import get_current_traceback
from werkzeug.contrib.profiler import ProfilerMiddleware

from nwrsc.controllers.admin import Admin
from nwrsc.controllers.dynamic import Announcer
from nwrsc.controllers.feed import Xml, Json
from nwrsc.controllers.register import Register
from nwrsc.controllers.results import Results
from nwrsc.lib.encoding import to_json
from nwrsc.model import Series
from nwrsc.merge.process import MergeProcess

log = logging.getLogger(__name__)

def create_app(config=None):
    """ Setup the application for the WSGI server """

    def errorlog(exception):
        """ We want to log exception information to file for later investigation """
        traceback = get_current_traceback(ignore_system_exceptions=True, show_hidden_frames=True)
        log.error(traceback.plaintext)
        last = traceback.frames[-1]
        now = datetime.datetime.now().replace(microsecond=0)
        return render_template("error.html", now=now, name=os.path.basename(last.filename), line=last.lineno, exception=exception)

    def preprocessor(endpoint, values):
        """ Remove the requirement for blueprint functions to put series/eventid in their function definitions """
        if values is not None:
            g.series = values.pop('series', None)
            g.eventid = values.pop('eventid', None)

    def urldefaults(endpoint, values):
        """ Make sure series,eventid from the subapp URLs are available for url_for relative calls """
        for u in ('series', 'eventid'):
            if u not in values and getattr(g, u) and current_app.url_map.is_endpoint_expecting(endpoint, u):
                values[u] = getattr(g, u)

    def t3(val, sign=False):
        """ Wrapper to safely print floats as XXX.123 format """
        if val is None: return ""
        if type(val) is not float: return str(val)
        try:
            return (sign and "%+0.3f" or "%0.3f") % (val,)
        except:
            return str(val)

    def msort(val, *attr):
        """ Filter to sort on multiple attributes """
        ret = list(val)
        ret.sort(key=attrgetter(*attr))
        return ret

    # setup uuid for postgresql
    psycopg2.extras.register_uuid()

    # Setup the application with default configuration
    theapp = Flask("nwrsc")
    theapp.config.update({
        "PORT":                    int(os.environ.get('NWRSC_PORT',     80)),
        "DEBUG":                  bool(os.environ.get('NWRSC_DEBUG',    False)),
        "PROFILE":                bool(os.environ.get('NWRSC_PROFILE',  False)),
        "DBHOST":                      os.environ.get('NWRSC_DBHOST',   '/var/run/postgresql'),
        "DBPORT":                  int(os.environ.get('NWRSC_DBPORT',   5432)),
        "DBUSER":                      os.environ.get('NWRSC_DBUSER',   'localuser'),
        "SHOWLIVE":               bool(os.environ.get('NWRSC_SHOWLIVE', True)),
        "LOG_LEVEL":                   os.environ.get('NWRSC_LOGLEVEL', 'INFO'),
        "SECRET_KEY":                  os.environ.get('NWRSC_SECRET',   'secret stuff here'),
        "ASSETS_DEBUG":           False,
        "LOGGER_HANDLER_POLICY":  "None",
    })

    theapp.config['TEMPLATES_AUTO_RELOAD'] = theapp.config['DEBUG']

    # Setup basic top level URL handling followed by Blueprints for the various sections
    theapp.url_value_preprocessor(preprocessor)
    theapp.url_defaults(urldefaults)
    theapp.add_url_rule('/',             'toresults', redirect_to='/results')
    theapp.register_blueprint(Admin,     url_prefix="/admin/<series>")
    theapp.register_blueprint(Announcer, url_prefix="/announcer/<series>")
    theapp.register_blueprint(Json,      url_prefix="/json/<series>")
    theapp.register_blueprint(Register,  url_prefix="/register")
    theapp.register_blueprint(Results,   url_prefix="/results/<series>")
    theapp.register_blueprint(Xml,       url_prefix="/xml/<series>")

    # Some static things that need to show up at the root level
    @theapp.route('/favicon.ico')
    def favicon(): return send_from_directory('static/images', 'cone.png')
    @theapp.route('/robots.txt')
    def robots(): return send_from_directory('static', 'robots.txt')
    @theapp.route('/<subapp>/')
    def serieslist(subapp): return render_template('serieslist.html', subapp=subapp, serieslist=Series.list())

    # Attach some handlers to the app
    @theapp.before_request
    def onrequest():
        g.db = psycopg2.connect(cursor_factory=psycopg2.extras.DictCursor, application_name="webserver", dbname="scorekeeper",
                                host=current_app.config['DBHOST'], port=current_app.config['DBPORT'], user=current_app.config['DBUSER'])
        if hasattr(g, 'series') and g.series:
            # Set up the schema path if we have a series
            g.seriestype = Series.type(g.series)
            if g.seriestype == Series.INVALID:
                abort(404, "%s is not a valid series" % g.series)
            with g.db.cursor() as cur:
                cur.execute("SET search_path=%s,'public'; commit; begin", (g.series,))
        else:
            g.seriestype = Series.UNKNOWN

    @theapp.teardown_request
    def teardown(exc=None):
        if hasattr(g, 'db'):
            g.db.close()
            del g.db # Removes 'db' from g dictionary

    @theapp.after_request
    def logrequest(response):
        log.info("%s %s?%s %s %s (%s)" % (request.method, request.path, request.query_string, response.status_code, response.content_length, response.content_encoding))
        return response

    # extra Jinja bits
    theapp.jinja_env.filters['t3'] = t3
    theapp.jinja_env.filters['msort'] = msort
    theapp.jinja_env.filters['to_json'] = to_json

    # If not running in debug mode (debug details to browser), log the traceback locally instead
    if not theapp.config['DEBUG']:
        theapp.register_error_handler(Exception, errorlog)

    # Configure our logging to use stderr so container host can log as they want
    level = getattr(logging, theapp.config['LOG_LEVEL'], logging.INFO) # turns 'INFO' string into logging.INFO int
    fmt  = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s', '%m/%d/%Y %H:%M:%S')
    shandler = StreamHandler()
    shandler.setFormatter(fmt)
    shandler.setLevel(level)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [shandler]

    logging.getLogger('werkzeug').setLevel(logging.WARN)

    # Setting up WebAssets, crypto stuff, compression and profiling
    Environment(theapp)
    Compress(theapp)
    if theapp.config.get('PROFILE', False):
        theapp.wsgi_app = ProfilerMiddleware(theapp.wsgi_app, restrictions=[30])
    theapp.hasher = Bcrypt(theapp)
    theapp.usts = URLSafeTimedSerializer(theapp.config["SECRET_KEY"])

    log.info("Scorekeeper App created")
    return theapp

