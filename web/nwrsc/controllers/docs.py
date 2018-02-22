"""
Use misaka to render our markdown docs and wrap them in our own template
"""

from flask import current_app, render_template, send_from_directory
from flask.helpers import safe_join
from flask_misaka import markdown
from nwrsc.controllers.blueprints import Docs

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

