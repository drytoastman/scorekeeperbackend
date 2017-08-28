#!/usr/bin/env python3

import base64
from collections import defaultdict
import datetime
import logging
import psycopg2
import psycopg2.extras
import queue
import random
import time
import uuid

import synclogic.model as model
from synclogic.model import MergeServer, PresentObjects, DeletedObjects

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
                        self.mergeWith(localdb, me, remote, passwords)

                    # Then check if there are any timeouts for local servers to merge with
                    for remote in MergeServer.getActive(localdb):
                        timeleft = (remote.lastcheck + self.waittime()) - datetime.datetime.utcnow()
                        if timeleft.total_seconds() < 0:
                            self.mergeWith(localdb, me, remote, passwords)

                    localdb.rollback() # Don't hang out in idle transaction from selects
            except Exception as e:
                log.error("Caught exception in main loop: {}".format(e), exc_info=e)

            # Wait for SCANTIME seconds before rescanning.  Wake immediately if something is dropped in the queue
            try:
                done = self.wakequeue.get(timeout=SCANTIME)
            except:
                pass


    def mergeWith(self, localdb, local, remote, passwords):
        log.debug("checking %s", remote.serverid)
        address = remote.address or remote.hostname
        with model.connectRemote(host=address, user='nulluser', password='nulluser') as remotedb:
            remote.updateSeriesFrom(remotedb)

        for series in remote.mergestate.keys():
            if series == 'public':
                continue
            if series not in passwords:
                log.debug("No password for %s, skipping", series)
                continue

            try:
                with model.connectRemote(host=address, user=series, password=passwords[series]) as remotedb:
                    assert series in local.mergestate, "series was not created in local database yet"
                    remote.updateCacheFrom(remotedb, 'public')
                    remote.updateCacheFrom(remotedb, series)

                    if remote.mergestate[series]['totalhash'] != local.mergestate[series]['totalhash']:
                        log.debug("Need to merge %s:", series)

                        # Obtain a merge lock on both sides and start the merge
                        with model.mergelocks(local, localdb, remote, remotedb):
                            ltables = local.mergestate[series]['hashes']
                            rtables = remote.mergestate[series]['hashes']
                            self.mergeTables(localdb, remotedb, set([k for k in ltables if ltables[k] != rtables[k]]))

                        # Rescan the tables to verify we are at the same state
                        remote.updateCacheFrom(remotedb, 'public')
                        remote.updateCacheFrom(remotedb, series)
                        local.updateCacheFrom(localdb, series)
                        remote.mergestate[series].pop('error', None)
            except Exception as e:
                remote.logSeriesError(series, str(e))
                log.warning("Merge with %s/%s failed: %s", remote.serverid, series, e, exc_info=e)

        remote.logMerge()


    def mergeTables(self, localdb, remotedb, tables):
        localmod    = {}
        localinsert = defaultdict(set)
        localupdate = defaultdict(set)
        localdelete = defaultdict(set)

        remotemod    = {}
        remoteinsert = defaultdict(set)
        remoteupdate = defaultdict(set)
        remotedelete = defaultdict(set)

        for t in tables:
            # Load pk/mod information from both databases
            localmod[t]  = PresentObjects.loadPresent(localdb, t)
            remotemod[t] = PresentObjects.loadPresent(remotedb, t)
            l = localmod[t].keyset()
            r = remotemod[t].keyset()

            # Keys in both databases
            for k in l & r:
                if localmod[t][k] == remotemod[t][k]:
                    # Same keys, same modification time, filter out now, no need to further process
                    del localmod[t][k]
                    del remotemod[t][k]
                    continue
                if localmod[t][k] > remotemod[t][k]:
                    remoteupdate[t].add(k)
                else:
                    localupdate[t].add(k)

            # Recalc as we probably removed alot of stuff in the previous step
            l = localmod[t].keyset()
            r = remotemod[t].keyset()

            # Only need to know about things deleted so far back in time based on mod times in other database
            ldeleted = DeletedObjects.deletedSince(localdb, t, remotemod[t].minmodtime())
            rdeleted = DeletedObjects.deletedSince(remotedb, t, localmod[t].minmodtime())

            # pk only in local database
            for pk in l - r:
                if rdeleted.contains(pk):
                    localdelete[t].add(pk)
                else:
                    remoteinsert[t].add(pk)

            # pk only in remote database
            for pk in r - l:
                if ldeleted.contains(pk):
                    remotedelete[t].add(pk)
                else:
                    localinsert[t].add(pk)

            log.debug("{}\n{}\n{}\n".format(localupdate, localinsert, localdelete))

        # Disable USER triggers

        for t in model.SERIES_TABLES.keys():  # Insert order first
            pass
        for t in reversed(model.SERIES_TABLES.keys()):  # Update/Delete order next
            pass

        # Renable USER triggers


