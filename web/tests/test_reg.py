#!/usr/bin/env python3

from flask import g
import logging
import os
import pytest
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))

import nwrsc.app 
import nwrsc.model

DRIVERID = '00000000-0000-0000-0000-000000000001'
CARID    = '00000000-0000-0000-0000-000000000002'
EVENTID  = '00000000-0000-0000-0000-000000000010'
HOST = '127.0.0.1'
PORT = 6432
USER = 'localuser'


@pytest.fixture(scope="session")
def database(request):
    if subprocess.run(["docker", "run", "-d", "--rm", "--name", "webdb", "-p", "6432:6432", "drytoastman/scdb:testdb"], stdout=subprocess.DEVNULL).returncode != 0:
        raise Exception("Failed to start webdb")
    def teardown():
        subprocess.run(["docker", "kill", "webdb"], stdout=subprocess.DEVNULL)
    request.addfinalizer(teardown)


@pytest.fixture(scope="session")
def webapp(): #database):
    nwrsc.app.logging_setup(logging.DEBUG, True, None)
    theapp = nwrsc.app.create_app()
    theapp.config['DBHOST'] = HOST
    theapp.config['DBPORT'] = PORT
    theapp.config['WTF_CSRF_ENABLED'] = False
    theapp.testing = True
    nwrsc.app.model_setup(theapp)
    return theapp.test_client()


def test_reg_insdel(webapp):

    db = nwrsc.model.AttrBase.connect(host=HOST, port=PORT, user=USER)
    with db.cursor() as cur:
        cur.execute("SET search_path='testseries','public'")
        cur.execute("SELECT * from registered")
        assert cur.rowcount == 0
        
        resp = webapp.post('/register/login', data={'login-username':'username', 'login-password':'password', 'login-submit':'Login'}, follow_redirects=True)
        resp = webapp.post('/register/testseries/eventspost', data={ 'eventid':EVENTID, CARID:'y' }, follow_redirects=True)
        cur.execute("SELECT * from registered")
        assert cur.rowcount == 1
        assert resp.status_code == 200

        resp = webapp.post('/register/testseries/eventspost', data={ 'eventid':EVENTID }, follow_redirects=True)
        cur.execute("SELECT * from registered")
        assert cur.rowcount == 0
        assert resp.status_code == 200


