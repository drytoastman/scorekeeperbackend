#!/usr/bin/env python3

from bs4 import BeautifulSoup
import logging
import os
import pytest
import subprocess
import sys
import time
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))

import nwrsc.app 
import nwrsc.model
from sccommon.logging import logging_setup

log = logging.getLogger('nwrsc.testhelpers')

def check_return(response):
    soup  = BeautifulSoup(response.data, "lxml")
    errormessages = soup.findAll('div', {'class': 'flash-message'})
    if errormessages:
        log.warning(errormessages)
        raise Exception(errormessages[0])
    if response.status_code != 200:
        log.warning(soup.get_text().encode('utf-8').decode('us-ascii', 'ignore'))
    assert response.status_code == 200


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
    if subprocess.run(["docker", "run", "-d", "--rm", "--name", "webdb", "-p", "{}:{}".format(webdata.port, webdata.port), "drytoastman/scdb:latest"], stdout=subprocess.DEVNULL).returncode != 0:
        raise Exception("Failed to start webdb")
    def teardown():
        subprocess.run(["docker", "kill", "webdb"], stdout=subprocess.DEVNULL)
    request.addfinalizer(teardown)

    for jj in range(10):
        try:
            db = nwrsc.model.AttrBase.connect(host=webdata.host, port=webdata.port, user='postgres')
            break
        except:
            time.sleep(1)
    else:
        raise Exception("unable to get connection to webdb")

    with db.cursor() as cur, open(os.path.join(os.path.dirname(__file__), 'testdata/basic.sql'), 'r') as fp:
        cur.execute("SELECT verify_user(%s, %s)",  (webdata.series, webdata.series))
        cur.execute("SELECT verify_series(%s)",    (webdata.series, ))
        cur.execute("SET search_path=%s,'public'", (webdata.series, ))
        for line in fp:
            sql = line.strip()
            if sql:
                cur.execute(sql)
        db.commit()
    return db


@pytest.fixture(scope="module")
def webapp(database, webdata):
    os.environ['DEBUG'] = "1"
    logging_setup()
    theapp = nwrsc.app.create_app()
    theapp.config['DBHOST'] = webdata.host
    theapp.config['DBPORT'] = webdata.port
    theapp.config['WTF_CSRF_ENABLED'] = False
    theapp.config['SUPER_ADMIN_PASSWORD'] = 'letmein'
    theapp.testing = True
    nwrsc.app.model_setup(theapp)
    webapp = theapp.test_client()
    webapp.post('/register/login', data={'login-username':'username', 'login-password':'password', 'login-submit':'Login'}, follow_redirects=True)
    webapp.post('/admin/{}/slogin'.format(webdata.series), data={'password':'letmein'}, follow_redirects=True)
    return webapp


@pytest.fixture(scope="module")
def webdb(webapp, webdata):  # webapp ensures database is up
    webdb = nwrsc.model.AttrBase.connect(host=webdata.host, port=webdata.port, user=webdata.user)
    with webdb.cursor() as cur:
        cur.execute("SET search_path=%s,'public'", (webdata.series,))
        webdb.commit();
    return webdb

