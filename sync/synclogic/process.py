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
from synclogic.model import DataInterface, PresentObject, DeletedObject, MergeServer

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
                with DataInterface.connectLocal() as localdb:
                    # Reset our world on each loop
                    model.initialize()

                    me = MergeServer.getLocal(localdb)
                    me.updateSeriesFrom(localdb)
                    for series in me.mergestate.keys():
                        me.updateCacheFrom(localdb, series)

                    passwords = DataInterface.loadPasswords(localdb)

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
        with DataInterface.connectRemote(host=address, user='nulluser', password='nulluser') as remotedb:
            remote.updateSeriesFrom(remotedb)

        for series in remote.mergestate.keys():
            if series not in passwords:
                log.debug("No password for %s, skipping", series)
                continue

            try:
                with DataInterface.connectRemote(host=address, user=series, password=passwords[series]) as remotedb:
                    assert series in local.mergestate, "series was not created in local database yet"
                    remote.updateCacheFrom(remotedb, series)

                    if remote.mergestate[series]['totalhash'] != local.mergestate[series]['totalhash']:
                        log.debug("Need to merge %s:", series)

                        # Obtain a merge lock on both sides and start the merge
                        with DataInterface.mergelocks(local, localdb, remote, remotedb):
                            # Shortcut for fresh download, just copy it all
                            if local.mergestate[series]['totalhash'] == '':
                                for t in model.TABLE_ORDER:
                                    DataInterface.copyTable(remotedb, localdb, series, t)
                            else:
                                ltables = local.mergestate[series]['hashes']
                                rtables = remote.mergestate[series]['hashes']
                                self.mergeTables(localdb, remotedb, set([k for k in ltables if ltables[k] != rtables[k]]))

                        # Rescan the tables to verify we are at the same state
                        remote.updateCacheFrom(remotedb, series)
                        local.updateCacheFrom(localdb, series)
                        remote.mergestate[series].pop('error', None)
            except Exception as e:
                remote.logSeriesError(series, str(e))
                log.warning("Merge with %s/%s failed: %s", remote.serverid, series, e, exc_info=e)

        remote.logMerge()


    def mergeTables(self, localdb, remotedb, tables):
        localinsert = defaultdict(list)
        localupdate = defaultdict(list)
        localdelete = defaultdict(list)

        remoteinsert = defaultdict(list)
        remoteupdate = defaultdict(list)
        remotedelete = defaultdict(list)

        for t in tables:
            # Load data from both databases, load it all in one go to be more efficient in updates later
            localobj  = PresentObject.loadPresent(localdb, t)
            remoteobj = PresentObject.loadPresent(remotedb, t)
            l = set(localobj.keys())
            r = set(remoteobj.keys())

            # Keys in both databases
            for pk in l & r:
                if localobj[pk].modified == remoteobj[pk].modified:
                    # Same keys, same modification time, filter out now, no need to further process
                    del localobj[pk]
                    del remoteobj[pk]
                    continue
                if localobj[pk].modified > remoteobj[pk].modified:
                    remoteupdate[t].append(localobj[pk])
                else:
                    localupdate[t].append(remoteobj[pk])

            # Recalc as we probably removed alot of stuff in the previous step
            l = set(localobj.keys())
            r = set(remoteobj.keys())

            # Only need to know about things deleted so far back in time based on mod times in other database
            ldeleted = DeletedObject.deletedSince( localdb, t,  PresentObject.minmodtime(remoteobj))
            rdeleted = DeletedObject.deletedSince(remotedb, t,  PresentObject.minmodtime(localobj))

            # pk only in local database
            for pk in l - r:
                if pk in rdeleted:
                    localdelete[t].append(rdeleted[pk])
                else:
                    remoteinsert[t].append(localobj[pk])

            # pk only in remote database
            for pk in r - l:
                if pk in ldeleted:
                    remotedelete[t].append(ldeleted[pk])
                else:
                    localinsert[t].append(remoteobj[pk])

            log.debug("{}  local {} {} {}".format(t,  len(localinsert[t]),  len(localupdate[t]),  len(localdelete[t])))
            log.debug("{} remote {} {} {}".format(t, len(remoteinsert[t]), len(remoteupdate[t]), len(remotedelete[t])))

        # Have to insert data starting from the top of any foreign key links
        # And then update/delete from the bottom of the same links

        # Insert order first (top down)
        for t in model.TABLE_ORDER:
            DataInterface.insert(localdb,  localinsert[t])
            DataInterface.insert(remotedb, remoteinsert[t])

        # Update/delete order next (bottom up)
        for t in reversed(model.TABLE_ORDER):
            DataInterface.update(localdb,  localupdate[t])
            DataInterface.update(remotedb, remoteupdate[t])

            DataInterface.delete(localdb,  localdelete[t])
            DataInterface.delete(remotedb, remotedelete[t])

