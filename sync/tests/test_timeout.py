#!/usr/bin/env python3

import datetime
import json
import logging
import pytest
import signal
import subprocess
import threading
import time

from helpers import *

log = logging.getLogger(__name__)

@pytest.mark.timeout(60, method='thread')
def test_networkoutage(syncdbs, syncdata):
    """ Testing network disconnects, should complete before pytest timeout """
    syncx, mergex = syncdbs

    signal.signal(signal.SIGHUP, lambda signum,frame: None)

    def action(action, table, localdb, remotedb, watcher):
        if action == 'update' and table == 'cars':
            # Simulate dead connection
            subprocess.run(["docker", "exec", "syncB", "iptables", "-P", "INPUT", "DROP"])
            subprocess.run(["docker", "exec", "syncB", "iptables", "-P", "OUTPUT", "DROP"])
    mergex['A'].listener = action

    # Modify firstname and address on A
    with syncx['A'].cursor() as cur:
        cur.execute("UPDATE drivers SET firstname=%s,attr=%s,modified=now() where driverid=%s", ('newfirst', json.dumps({'address': '123'}), syncdata.driverid,))
        cur.execute("UPDATE cars SET number=666,modified=now() where carid=%s", (syncdata.carid,))
        syncx['A'].commit()
    time.sleep(0.1)

    dosync(syncx['A'], mergex['A'])

    subprocess.run(["docker", "exec", "syncB", "iptables", "-P", "INPUT", "ACCEPT"])
    subprocess.run(["docker", "exec", "syncB", "iptables", "-P", "OUTPUT", "ACCEPT"])


@pytest.mark.timeout(30, method='thread')
def test_longblock(syncdbs, syncdata, dataentry):
    """ Testing blocking of a database connection for too long """
    syncx, mergex = syncdbs
    despan = None

    def dataentrywork():
        nonlocal despan
        with dataentry.cursor() as cur:
            destart = time.time()
            cur.execute("UPDATE runs SET status='DNF',modified=now()")
            dataentry.commit()
            despan = time.time() - destart

    def action(action, table, localdb, remotedb, watcher):
        if action == 'update' and table == 'cars':
            # Pretend we are working on the remote side, artificially lock local runs table, start a data entry action to update runs and then hang out
            watcher.remote()
            with localdb.cursor() as cur:
                cur.execute("lock runs")
                threading.Thread(target=dataentrywork, daemon=True).start()
                for ii in range(10):
                    cur.execute("select application_name,pid from pg_stat_activity")
                    if cur.rowcount: log.debug("activity = {}".format(cur.fetchall()))
                    time.sleep(1)
    mergex['A'].listener = action 

    # Make some mods so that sync starts
    with syncx['A'].cursor() as cur:
        cur.execute("UPDATE cars SET number=666,modified=now() where carid=%s", (syncdata.carid,))
        syncx['A'].commit()
    time.sleep(0.1)

    syncstart = time.time()
    dosync(syncx['A'], mergex['A'])
    syncspan = time.time() - syncstart
    time.sleep(0.1)

    assert(despan and despan >= 3.0 and despan < 3.6)
    assert(syncspan < 5)
    with syncx['A'].cursor() as cur:
        cur.execute("SELECT * FROM runs WHERE status!='DNF'")
        assert(cur.rowcount == 0)

