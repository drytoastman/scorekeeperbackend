#!/usr/bin/env python3

import pytest

from conftest import check_return

def test_event_classorder(webapp, webdb, webdata):
    # Set class order, should balk at groups with intersected classes
    with pytest.raises(Exception):
        check_return(webapp.post('/admin/{}/event/{}/rungroups'.format(webdata.series, webdata.eventid), data = {'group1':'c1', 'group2':'c1,c2'}, follow_redirects=True))
    check_return(webapp.post('/admin/{}/event/{}/rungroups'.format(webdata.series, webdata.eventid), data = {'group1':'c1,c2', 'group2':'c3,c4'}, follow_redirects=True))

    # Now get the result
    check_return(webapp.get('/admin/{}/event/{}/rungroups'.format(webdata.series, webdata.eventid), follow_redirects=True))
