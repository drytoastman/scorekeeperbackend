#!/usr/bin/env python3

def test_(webapp, webdb, webdata):

    url = '/admin/{}/newseries'.format(webdata.series)
    resp = webapp.post(url, data={ 'name':'newseries' }, follow_redirects=True)
    print(resp.data)

    with webdb.cursor() as cur:
        cur.execute("SELECT * from newseries.indexlist")
        for r in cur.fetchall():
            print(r)
        assert cur.rowcount == 1

