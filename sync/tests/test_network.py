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
from synclogic.model import DataInterface

log = logging.getLogger(__name__)

def _simplemod(syncx, syncdata):
    syncdata.simplename   = getattr(syncdata, 'simplename',   'simplefirst')  + '1'
    syncdata.simplenumber = getattr(syncdata, 'simplenumber', 666) + 1
    with syncx['A'].cursor() as cur:
        cur.execute("UPDATE drivers SET firstname=%s,modified=now() where driverid=%s", (syncdata.simplename, syncdata.driverid,))
        cur.execute("UPDATE cars SET number=%s,modified=now() where carid=%s", (syncdata.simplenumber, syncdata.carid,))
        syncx['A'].commit()
    time.sleep(0.1)

def _simpleverify(syncx, syncdata):
    verify_driver(syncx, syncdata.driverid, (('firstname', syncdata.simplename),), ())
    verify_car(syncx, syncdata.carid, (('number', syncdata.simplenumber),), ())

def _syncBnetdown():
    subprocess.run(["docker", "exec", "syncB", "iptables", "-P", "INPUT", "DROP"])
    subprocess.run(["docker", "exec", "syncB", "iptables", "-P", "OUTPUT", "DROP"])

def _syncBnetup():
    subprocess.run(["docker", "exec", "syncB", "iptables", "-P", "INPUT", "ACCEPT"])
    subprocess.run(["docker", "exec", "syncB", "iptables", "-P", "OUTPUT", "ACCEPT"])



def test_delayednetwork(syncdbs, syncdata):
    """ Test over a network with major delay or loss issues """
    syncx, mergex = syncdbs
    caught = None

    def action(action, table, exception=None, **kwargs):
        nonlocal caught
        if action == 'exception':
            caught = exception
    mergex['A'].listener = action

    _simplemod(syncx, syncdata)

    # Run sync with delay and drop issues
    subprocess.run("docker exec syncB tc qdisc add dev eth0 root netem delay 800ms 100ms 25% loss 0.1% 25%".split())
    dosync(syncx['A'], mergex['A'])
    subprocess.run("docker exec syncB tc qdisc del dev eth0 root".split())

    if caught: raise caught
    _simpleverify(syncx, syncdata)



@pytest.mark.timeout(DataInterface.PEER_TIMEOUT+20, method='thread')
def test_networkoutage(syncdbs, syncdata):
    """ Testing network disconnects, should complete before pytest timeout """
    syncx, mergex = syncdbs
    signal.signal(signal.SIGHUP, lambda x,y: None)
    firstrun = True

    def action(action, subject, **kwargs):
        nonlocal firstrun
        if firstrun and action == 'update' and subject == 'cars':
            _syncBnetdown()
            firstrun = False
    mergex['A'].listener = action

    _simplemod(syncx, syncdata)

    # Run the initial sync which will invoke the netdown, then return to netup
    x = time.time()
    dosync(syncx['A'], mergex['A'])
    syncspan = time.time() - x
    assert(syncspan < DataInterface.PEER_TIMEOUT+3)
    _syncBnetup()

    # Another sync should succeeed now
    dosync(syncx['A'], mergex['A'])
    _simpleverify(syncx, syncdata)



@pytest.mark.timeout(30, method='thread')
def test_longblock(syncdbs, syncdata, dataentry):
    """ Testing blocking of a database connection for too long """
    syncx, mergex = syncdbs
    despan = None

    def dataentrywork():
        nonlocal despan
        with dataentry.cursor() as cur:
            try:
                x = time.time()
                cur.execute("UPDATE runs SET status='DNF',modified=now()")
                dataentry.commit()
                despan = time.time() - x
            except Exception as e:
                logging.error("dataentrywork failure: %s", e, exc_info=e)

    def action(action, subject, localdb=None, remotedb=None, watcher=None, **kwargs):
        if action == 'update' and subject == 'cars':
            # Pretend we are working on the remote side, artificially lock local runs table, start a data entry action to update runs and then hang out
            watcher.remote()
            with localdb.cursor() as cur:
                cur.execute("lock runs")
                threading.Thread(target=dataentrywork, daemon=True).start()
                for ii in range(10):
                    cur.execute("select application_name,pid from pg_stat_activity")
                    if cur.rowcount > 0:
                        log.debug("activity = {}".format(cur.fetchall()))
                    time.sleep(1)
    mergex['A'].listener = action

    _simplemod(syncx, syncdata)

    x = time.time()
    dosync(syncx['A'], mergex['A'])
    syncspan = time.time() - x
    while not despan:
        time.sleep(0.1)

    # Verify our runtimes and that the dataentry setting of all runs to DNF took place
    assert(despan and despan >= DataInterface.APP_TIME_LIMIT and despan < DataInterface.APP_TIME_LIMIT + 1.0)
    assert(syncspan < DataInterface.APP_TIME_LIMIT+3.0)
    with syncx['A'].cursor() as cur:
        cur.execute("SELECT * FROM runs WHERE status!='DNF'")
        assert(cur.rowcount == 0)

