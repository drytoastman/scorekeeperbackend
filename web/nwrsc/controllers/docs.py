"""
Use misaka to render our markdown docs and wrap them in our own template
"""

from flask import current_app, g, render_template, send_from_directory
from flask_assets import Bundle
from flask.helpers import safe_join
from flask_misaka import markdown
from nwrsc.controllers.blueprints import Docs

@Docs.before_app_first_request
def init():
    env = current_app.jinja_env.assets_environment
    env.register('docs.js',  Bundle(env.j['jquery'], env.j['bootstrap'], env.j['barcodes'], "js/common.js", filters="rjsmin", output="docs.js"))
    env.register('docs.css', Bundle("scss/docs.scss", depends="scss/*.scss", filters="libsass", output="docs.css"))

@Docs.before_request
def setup():
    g.title = 'Scorekeeper Documentation'

@Docs.route("/")
def index():
    return render_template("docs/wrapper.html")

@Docs.route("/<selection>")
def docpage(selection):
    with current_app.open_resource(safe_join("templates/docs", selection), 'r') as f:
        return render_template("docs/wrapper.html", content=markdown(f.read()))

@Docs.route("/images/<selection>")
def image(selection):
    return send_from_directory("static/images", selection)

