#!/usr/bin/env python3

import logging
import os
import pytest
import subprocess
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))

import nwrsc.app 
import nwrsc.model

@pytest.fixture(scope="module")
def webdata():
    return types.SimpleNamespace(
        driverid = '00000000-0000-0000-0000-000000000001',
        carid    = '00000000-0000-0000-0000-000000000002',
        eventid  = '00000000-0000-0000-0000-000000000010',
        host     = '127.0.0.1',
        port     =  6432,
        user     = 'localuser',
        series   = 'testseries')


@pytest.fixture(scope="module")
def database(request, webdata):
    if subprocess.run(["docker", "run", "-d", "--rm", "--name", "webdb", "-p", "{}:{}".format(webdata.port, webdata.port), "drytoastman/scdb:testdb"], stdout=subprocess.DEVNULL).returncode != 0:
        raise Exception("Failed to start webdb")
    def teardown():
        subprocess.run(["docker", "kill", "webdb"], stdout=subprocess.DEVNULL)
    request.addfinalizer(teardown)


@pytest.fixture(scope="module")
def webapp(database, webdata):
    nwrsc.app.logging_setup(logging.DEBUG, True, None)
    theapp = nwrsc.app.create_app()
    theapp.config['DBHOST'] = webdata.host
    theapp.config['DBPORT'] = webdata.port
    theapp.config['WTF_CSRF_ENABLED'] = False
    theapp.testing = True
    nwrsc.app.model_setup(theapp)
    webapp = theapp.test_client()
    webapp.post('/register/login', data={'login-username':'username', 'login-password':'password', 'login-submit':'Login'}, follow_redirects=True)
    return webapp


@pytest.fixture(scope="module")
def webdb(webapp, webdata):  # webapp ensures database is up
    webdb = nwrsc.model.AttrBase.connect(host=webdata.host, port=webdata.port, user=webdata.user)
    with webdb.cursor() as cur:
        cur.execute("SET search_path=%s,'public'", (webdata.series,))
        webdb.commit();
    return webdb

