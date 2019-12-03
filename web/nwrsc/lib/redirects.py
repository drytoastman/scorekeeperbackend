import logging

from flask import current_app, redirect, request, url_for
from nwrsc.model import LocalInfo

log = logging.getLogger(__name__)

def redirect_by_host():
    current_app.config['SERVER_NAME'] = LocalInfo.getMyAddress()
    if request.host.startswith('result'):
        return redirect(url_for("Results.base", _external=True))

