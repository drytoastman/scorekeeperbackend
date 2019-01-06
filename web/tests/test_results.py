#!/usr/bin/env python3

from conftest import check_return

def test_event_result(webapp, webdb, webdata):
    check_return(webapp.get('/results/{}/event/{}'.format(webdata.series, webdata.eventid), follow_redirects=True))

def test_event_audit(webapp, webdb, webdata):
    check_return(webapp.get('/results/{}/event/{}/audit'.format(webdata.series, webdata.eventid), follow_redirects=True))

def test_event_announcer(webapp, webdb, webdata):
    check_return(webapp.get('/announcer/{}/event/{}/next?lastresult=0'.format(webdata.series, webdata.eventid), follow_redirects=True))

def test_champ_sorting():
    import datetime
    import operator
    from nwrsc.model.result import ChampEntrant
    from nwrsc.model.event import Event

    events = [Event(eventid='abc', date=datetime.datetime.now(), champrequire=True,  useastiebreak=False), 
              Event(eventid='xyz', date=datetime.datetime.now(), champrequire=True,  useastiebreak=False), 
              Event(eventid='123', date=datetime.datetime.now(), champrequire=False, useastiebreak=True)]

    def eresult(*results):
        ret = ChampEntrant()
        for ii, r in enumerate(results):
            if len(r) > 1:
                ret.addResults(events[ii], {'firstname':'', 'lastname':'', 'driverid':'', 'position':r[0], 'points':r[1]})
        ret.finalize(3, events)
        return ret

    # en2 should be first as they won the specific last event
    en1 = eresult((4,11), (5,9), (6,7))
    en2 = eresult((6,7), (4,11), (5,9))
    results = [en1, en2]
    results.sort(key=operator.attrgetter('points', 'tiebreakers'), reverse=True)
    assert(results == [en2, en1])

    # en2 should be first as they had the 6th place finish
    en1 = eresult((7,6), (10,3), ())
    en2 = eresult((12,1), (12,1), (6,7))
    results = [en1, en2]
    results.sort(key=operator.attrgetter('points', 'tiebreakers'), reverse=True)
    assert(results == [en2, en1])

