import datetime
from operator import attrgetter
import os
import logging
import re
import sys
import time
from traceback import format_tb

from flask import Flask, request, abort, g, current_app, message_flashed, render_template, send_from_directory
from flask_assets import Environment
from flask_compress import Compress
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer
from jinja2 import ChoiceLoader, FunctionLoader
from werkzeug.contrib.profiler import ProfilerMiddleware
from werkzeug.debug.tbtools import get_current_traceback
from werkzeug.exceptions import HTTPException


from .controllers import *
from .lib.encoding import time_print, to_json
from .lib.misc import *
from .model import AttrBase, Series, Settings

log = logging.getLogger(__name__)

def create_app():
    """ Setup the application for the WSGI server """

    ### Configuration
    theapp = Flask("nwrsc")
    theapp.config.update({
        "ASSETS_DEBUG":           any2bool(os.environ.get('DEBUG',                 False)),
        "DEBUG":                  any2bool(os.environ.get('DEBUG',                 False)),
        "PAYMENT_FAKE":           any2bool(os.environ.get('PAYMENT_FAKE',          False)),
        "DBHOST":                          os.environ.get('DBHOST',                '/var/run/postgresql'),
        "DBPORT":                      int(os.environ.get('DBPORT',                5432)),
        "DBUSER":                          os.environ.get('DBUSER',                'localuser'),
        "IS_MAIN_SERVER":         any2bool(os.environ.get('IS_MAIN_SERVER',        False)),
        "MAX_CONTENT_LENGTH":                                                      2 * 1024 * 1024,
        "ONSITE":                 any2bool(os.environ.get('ONSITE',                False)),
        "PROFILE":                any2bool(os.environ.get('PROFILE',               False)),
        "PROPAGATE_EXCEPTIONS":                                                    False,
        "SECRET_KEY":                      os.environ.get('FLASK_SECRET',         'replaced by environment for laptops, secrets.json for server'),
        "SECRETS_FILE":                    os.environ.get('SECRETS_FILE',          None),
        "SQ_APPLICATION_ID":               os.environ.get('SQ_APPLICATION_ID',     None),
        "SQ_APPLICATION_SECRET":           os.environ.get('SQ_APPLICATION_SECRET', None),
        "SHOWLIVE":               any2bool(os.environ.get('SHOWLIVE',              True)),
        "SUPER_ADMIN_PASSWORD":            os.environ.get('SUPER_ADMIN_PASSWORD',  None),
        "UI_TIME_ZONE":                    os.environ.get('UI_TIME_ZONE',          'US/Pacific'),
        "UPLOAD_FOLDER":                                                           '/var/uploads',
    })

    theapp.config['TEMPLATES_AUTO_RELOAD'] = theapp.config['DEBUG']
    theapp.config['LIBSASS_STYLE']         = theapp.config['DEBUG'] and 'expanded' or 'compressed'

    if theapp.config['SECRETS_FILE']:
        theapp.config.from_json(theapp.config['SECRETS_FILE'])

    if not os.path.isdir(theapp.config['UPLOAD_FOLDER']):
        log.warning("Upload folder not present, uploads will be disabled")
        del theapp.config['UPLOAD_FOLDER']

    ### WebAssets
    assets   = Environment(theapp)
    assets.from_module('nwrsc.assets')

    ### URL handling and Blueprints for the various sections
    theapp.add_url_rule('/',             'toresults', redirect_to='/results')
    theapp.register_blueprint(Admin,     url_prefix="/admin/<series>")
    theapp.register_blueprint(Announcer, url_prefix="/announcer/<series>")
    theapp.register_blueprint(Api,       url_prefix="/api")
    theapp.register_blueprint(Docs,      url_prefix="/docs")
    theapp.register_blueprint(Register,  url_prefix="/register")
    theapp.register_blueprint(Results,   url_prefix="/results/<series>")
    theapp.add_url_rule('/admin/squareoauth', "Admin.squareoauth")
    theapp.add_url_rule('/admin/',       "Admin.base")
    theapp.add_url_rule('/announcer/',   "Announcer.base")
    theapp.add_url_rule('/results/',     "Results.base")

    @theapp.route('/favicon.ico')
    def favicon(): return send_from_directory('static/images', 'cone.png')
    @theapp.route('/robots.txt')
    def robots(): return send_from_directory('static', 'robots.txt')
    @theapp.route('/api/swagger.yaml')
    def resultsfeed(): return send_from_directory('api', 'swagger.yaml')

    @theapp.url_value_preprocessor
    def preprocessor(endpoint, values):
        """ Remove the requirement for blueprint functions to put series/eventid in their function definitions """
        if values is not None:
            g.series = values.pop('series', None)
            g.eventid = values.pop('eventid', None)
            g.challengeid = values.pop('challengeid', None)

    @theapp.url_defaults
    def urldefaults(endpoint, values):
        """ Make sure series,eventid from the subapp URLs are available for url_for relative calls """
        for u in ('series', 'eventid', 'challengeid'):
            if u not in values and getattr(g, u, None) and current_app.url_map.is_endpoint_expecting(endpoint, u):
                values[u] = getattr(g, u)

    ## Before, After and Teardown request
    @theapp.before_request
    def onrequest():
        g.db = AttrBase.connect(host=current_app.config['DBHOST'], port=current_app.config['DBPORT'], user=current_app.config['DBUSER'])
        if hasattr(g, 'series') and g.series:
            # Set up the schema path if we have a series
            g.seriestype = Series.type(g.series)
            if g.seriestype == Series.INVALID:
                raise InvalidSeriesException()
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
        if not response.cache_control.max_age: # Not set somewhere else, set to no-cache
            response.headers['Expires'] = '-1'
            response.last_modified = datetime.datetime.now()
            response.pragma = 'no-cache'
            response.cache_control.no_store = True
            response.cache_control.no_cache = True
            response.cache_control.must_revalidate = True
            response.cache_control.max_age = 0

        log.debug("%s %s?%s %s %s (%s)" % (request.method, request.path, request.query_string, response.status_code, response.content_length, response.content_encoding))
        return response


    ### Error Handlers
    @theapp.errorhandler(InvalidSeriesException)
    def invalidseries(e):
        return render_template("common/simple.html", header="404 No Such Series", content="There is no series present with that name"), 404

    @theapp.errorhandler(InvalidEventException)
    def invalidevent(e):
        return render_template("common/simple.html", header="404 No Such Event", content="There is no event present with that id"), 404

    @theapp.errorhandler(InvalidChallengeException)
    def invalidchallenge(e):
        return render_template("common/simple.html", header="404 No Such Challenge", content="There is no challenge present with that id"), 404

    @theapp.errorhandler(ArchivedSeriesException)
    def nonactiveseries(e):
        return render_template("common/simple.html", header="410 Archived Series", content="This series is archived and the requested page is not available for archived series"), 410

    @theapp.errorhandler(NotLoggedInException)
    def notloggedin(e):
        return render_template("common/simple.html", header="403 Not Logged In", content="You are not logged in and cannot access this resource."), 403

    @theapp.errorhandler(DisplayableError)
    def displayable(e):
        log.info(e.content, exc_info=e.__cause__ and e or None)
        return render_template("common/simple.html", header=e.header, content=e.content), 500

    @message_flashed.connect_via(theapp)
    def log_flashes(sender, message, category):
        if 'Invalid username/password' not in message:
            log.warning("Flashed: " + message)

    @theapp.errorhandler(Exception)
    @theapp.errorhandler(500)
    def errorlog(e):
        """ We want to log exception information to file for later investigation when debugger framework isn't presenting it for us and present a simple reportable error for user """
        if isinstance(e, HTTPException): # and (500 <= e.code < 600):
            return e
        traceback = get_current_traceback(ignore_system_exceptions=True, show_hidden_frames=True)
        last = traceback.frames[-1]
        now = datetime.datetime.now().replace(microsecond=0)
        return render_template("common/error.html", now=now, name=os.path.basename(last.filename), line=last.lineno, exception=e, tbstring=theapp.debug and traceback.plaintext), 500


    #### Jinja
    theapp.jinja_env.filters['timeprint'] = time_print
    theapp.jinja_env.filters['t3'] = t3
    theapp.jinja_env.filters['d2'] = d2
    theapp.jinja_env.filters['msort'] = msort
    theapp.jinja_env.filters['to_json'] = to_json
    theapp.jinja_env.tests['htmlstr'] = hashtml

    def custom_template_loader(request):
        # Allows us to %include templates from the database settings values
        name = request.split('%')
        if name[0] in Settings.DEFAULTS:
            if hasattr(g, 'seriesinfo'): # archived results
                rv = getattr(g.settings, name[0], "")
            else:
                rv = Settings.get(name[0])
            if len(rv.strip()):
                return rv
        return None
    theapp.jinja_loader = ChoiceLoader([ theapp.jinja_loader, FunctionLoader(custom_template_loader) ])


    ### Crypto, Compression and optional Profiling
    theapp.hasher = Bcrypt(theapp)
    theapp.usts = URLSafeTimedSerializer(theapp.config["SECRET_KEY"])
    Compress(theapp)
    if theapp.config.get('PROFILE', False):
        theapp.wsgi_app = ProfilerMiddleware(theapp.wsgi_app, restrictions=[30])

    ### Reverse Proxy handler
    theapp.wsgi_app = ReverseProxied(theapp.wsgi_app)

    log.info("Scorekeeper App created")
    return theapp


class ReverseProxied(object):
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        if environ.get('HTTP_X_FORWARDED_PROTO', '') == 'https' or environ.get('HTTP_X_FORWARDED_PORT', '80') == '443':
            environ['wsgi.url_scheme'] = 'https'

        server = environ.get('HTTP_X_FORWARDED_SERVER', '').split(',')[0]
        if server: environ['HTTP_HOST'] = server
        return self.app(environ, start_response)


def cron_jobs():
    from nwrsc.controllers.payments import paymentscron
    dbapp = Flask("dbapp")
    dbapp.config.update({
        "DEBUG":                  any2bool(os.environ.get('DEBUG',                 False)),
        "DBHOST":                          os.environ.get('DBHOST',                '/var/run/postgresql'),
        "DBPORT":                      int(os.environ.get('DBPORT',                5432)),
        "DBUSER":                          os.environ.get('DBUSER',                'localuser'),
        "SECRETS_FILE":                    os.environ.get('SECRETS_FILE',          None),
        "UI_TIME_ZONE":                    os.environ.get('UI_TIME_ZONE',          'US/Pacific'),
    })
    if dbapp.config['SECRETS_FILE']:
        dbapp.config.from_json(dbapp.config['SECRETS_FILE'])
    model_setup(dbapp)

    with dbapp.app_context():
        g.db = AttrBase.connect(host=dbapp.config['DBHOST'], port=dbapp.config['DBPORT'], user=dbapp.config['DBUSER'], app='cronjobs')
        paymentscron()


def model_setup(app):
    # Database introspection at startup
    with app.app_context():
        while True:
            try:
                AttrBase.initialize(host=app.config['DBHOST'], port=app.config['DBPORT'])
                break
            except Exception as e:
                log.info("Error during model initialization, waiting for db and template: %s", e)
                time.sleep(5)
        log.info("Scorekeeper DB models initialized")
