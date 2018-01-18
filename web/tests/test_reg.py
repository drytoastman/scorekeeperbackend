#!/usr/bin/env python3

def test_reg_insdel(webapp, webdb, webdata):

    url = '/register/{}/eventspost'.format(webdata.series)

    with webdb.cursor() as cur:
        cur.execute("SELECT * from registered")
        assert cur.rowcount == 0
        
        resp = webapp.post(url, data={ 'eventid':webdata.eventid, webdata.carid:'y' }, follow_redirects=True)
        cur.execute("SELECT * from registered")
        assert cur.rowcount == 1
        assert resp.status_code == 200

        resp = webapp.post(url, data={ 'eventid':webdata.eventid}, follow_redirects=True)
        cur.execute("SELECT * from registered")
        assert cur.rowcount == 0
        assert resp.status_code == 200

