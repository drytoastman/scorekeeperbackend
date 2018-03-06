#!/usr/bin/env python3

from flask import g
import nwrsc.app

# Load the base app without debug and force webassets to generate our filtered resources
# Only used when building an image for deployment.  All of these files are ignored by .gitignore
app = nwrsc.app.create_app()
with app.app_context():
    g.series = ''
    g.eventid = ''
    g.challengeid = ''
    for f in app.before_first_request_funcs:
        f()
    for bundle in app.jinja_env.assets_environment:
        print(bundle.urls())

