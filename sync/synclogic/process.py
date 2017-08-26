#!/usr/bin/env python3

import base64
import datetime
import logging
import psycopg2
import psycopg2.extras
import queue
import random
import uuid

import synclogic.model as model
from synclogic.model import MergeServer

log  = logging.getLogger(__name__)

SCANTIME = 10
WAITTIME = 30

class MergeProcess():
    # If we have the greater serverid, I am the leader and should be doing the work
    # Still fall back and try a merge ourselves if the leader isn't doing anything

    def __init__(self):
        psycopg2.extras.register_uuid()
        self.wakequeue = queue.Queue()

    def waittime(self):
        return datetime.timedelta(seconds=(WAITTIME + random.uniform(-5, +5)))

    def shutdown(self):
        self.wakequeue.put(True)

    def poke(self):
        self.wakequeue.put(False)

    def runforever(self):
        done = False
        while not done:
            try:
                with model.connectLocal() as localdb:
                    # Reset our world on each loop
                    me = MergeServer.getLocal(localdb)
                    me.updateSeriesFrom(localdb)
                    for series in me.mergestate.keys():
                        me.updateCacheFrom(localdb, series)

                    passwords = model.loadPasswords(localdb)

                    # First merge with anyone the user told us to right away
                    for remote in MergeServer.getNow(localdb):
                        self.mergeWith(me, remote, passwords)

                    # Then check if there are any timeouts for local servers to merge with
                    for remote in MergeServer.getActive(localdb):
                        timeleft = (remote.lastcheck + self.waittime()) - datetime.datetime.utcnow()
                        if timeleft.total_seconds() < 0:
                            self.mergeWith(me, remote, passwords)

                    localdb.rollback() # Don't hang out in idle transaction from selects
            except Exception as e:
                log.error("Caught exception in main loop: {}".format(e), exc_info=e)

            # Wait for SCANTIME seconds before rescanning.  Wake immediately if something is dropped in the queue
            try:
                done = self.wakequeue.get(timeout=SCANTIME)
            except:
                pass


    def mergeWith(self, local, remote, passwords):
        log.debug("checking %s", remote.serverid)
        address = remote.address or remote.hostname
        with model.connectRemote(host=address, user='nulluser', password='nulluser') as remotedb:
            remote.updateSeriesFrom(remotedb)

        for series in remote.mergestate.keys():
            if series not in passwords:
                log.debug("No password for %s, skipping", series)
                continue
            with model.connectRemote(host=address, user=series, password=passwords[series]) as remotedb:
                remote.updateCacheFrom(remotedb, series)
                if remote.mergestate[series]['all'] != local.mergestate[series]['all']:
                    log.debug("Need to merge %s here.", series)

        remote.logMerge()


def amleader(myid, remoteid):
    return myid < remoteid

