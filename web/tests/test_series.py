#!/usr/bin/env python3

def test_newseries(webapp, webdb, webdata):

    url = '/admin/{}/newseries'.format(webdata.series)

    # Copy classes true
    resp = webapp.post(url, data={ 'name':'newseries1', 'password': 'password', 'copyclasses': 'y' }, follow_redirects=True)
    with webdb.cursor() as cur:
        cur.execute("SELECT * from newseries1.indexlist where indexcode=''")
        assert cur.rowcount == 1

    # Copy classes off
    resp = webapp.post(url, data={ 'name':'newseries2', 'password': 'password' }, follow_redirects=True)
    with webdb.cursor() as cur:
        cur.execute("SELECT * from newseries2.indexlist where indexcode=''")
        assert cur.rowcount == 1

