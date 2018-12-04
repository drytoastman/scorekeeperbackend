#!/usr/bin/env python3

from conftest import check_return

def test_event_result(webapp, webdb, webdata):
    check_return(webapp.get('/results/{}/event/{}'.format(webdata.series, webdata.eventid), follow_redirects=True))

def test_event_audit(webapp, webdb, webdata):
    check_return(webapp.get('/results/{}/event/{}/audit'.format(webdata.series, webdata.eventid), follow_redirects=True))

def test_event_announcer(webapp, webdb, webdata):
    check_return(webapp.get('/announcer/{}/event/{}/next?lastresult=0'.format(webdata.series, webdata.eventid), follow_redirects=True))


