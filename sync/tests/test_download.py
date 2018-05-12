#!/usr/bin/env python3

import json
import pytest
import os
import time

from helpers import *

hostname = "scorekeeper.wwscc.org"
series   = os.environ.get('SERIES', None)
password = os.environ.get('PASSWORD', None)

@pytest.mark.skipif(not series or not password, reason="no series or password set")
def test_download(sync1db, syncdata):
    """ Test a download from the main server for timeout behavior """
    sync, merge = sync1db

    with sync.cursor() as cur:
        cur.execute("DROP SCHEMA testseries CASCADE")
        cur.execute("DELETE FROM drivers")
        cur.execute("DELETE FROM publiclog")
        cur.execute("SELECT verify_user(%s, %s)",  (series, password))
        cur.execute("SELECT verify_series(%s)",    (series, ))
        cur.execute("SET search_path=%s,'public'", (series, ))
        cur.execute("INSERT INTO mergeservers(serverid, hostname, address, ctimeout, hoststate) VALUES ('00000000-0000-0000-0000-123456789012', %s, '', 10, '1')", (hostname,))
        sync.commit()

    merge.runonce()

    with sync.cursor() as cur:
        cur.execute("select mergestate->%s->'error' from mergeservers where hostname=%s", (series,hostname))
        error = cur.fetchone()[0]
        assert(not error)

