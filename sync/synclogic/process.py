#!/usr/bin/env python3

import base64
from collections import defaultdict
import datetime
import logging
import psycopg2
import psycopg2.extras
import queue
import time
import uuid

from synclogic.model import *

log  = logging.getLogger(__name__)
signalled = False

class SkipThisRound(Exception):
    pass

class MergeProcess():

    def __init__(self):
        psycopg2.extras.register_uuid()
        self.wakequeue = queue.Queue()

    def shutdown(self):
        """ Interrupt what we are doing and quite """
        global signalled
        signalled = True
        self.wakequeue.put(True)

    def poke(self):
        """ Just wake the queue wait, don't interrupt current work """
        self.wakequeue.put(False)

    def runforever(self):
        while True:
            try:
                DataInterface.initialize()
                break
            except Exception as e:
                log.info("Error during model initialization, waiting for db and template: %s", e)
                time.sleep(5)
        log.info("Sync DB models initialized")

        done = False
        while not done:
            try:
                global signalled
                signalled = False
                with DataInterface.connectLocal() as localdb:
                    # Reset our world on each loop
                    me = MergeServer.getLocal(localdb)
                    me.updateSeriesFrom(localdb)
                    for series in me.mergestate.keys():
                        me.updateCacheFrom(localdb, series)

                    passwords = DataInterface.loadPasswords(localdb)

                    # Check if there are any timeouts for servers to merge with
                    for remote in MergeServer.getActive(localdb):
                        if remote.nextcheck < datetime.datetime.utcnow():
                            try:
                                self.mergeWith(localdb, me, remote, passwords)
                            except Exception as e:
                                log.error("Caught exception merging with {}: {}".format(remote, e), exc_info=e)
                                remote.serverError(str(e))

                    localdb.rollback() # Don't hang out in idle transaction from selects

            except (NoDatabaseException, NoLocalHostServer) as ie:
                log.debug(type(ie).__name__)

            except Exception as e:
                log.error("Caught exception in main loop: {}".format(e), exc_info=e)

            # Wait for 10 seconds before rescanning.  Wake immediately if something is dropped in the queue
            try:
                done = self.wakequeue.get(timeout=10)
            except:
                pass


    def mergeWith(self, localdb, local, remote, passwords):
        global signalled

        log.debug("checking %s", remote)
        with DataInterface.connectRemote(server=remote, user='nulluser', password='nulluser') as remotedb:
            remote.updateSeriesFrom(remotedb)

        for series in remote.mergestate.keys():
            error = None
            if series not in passwords:
                log.debug("No password for %s, skipping", series)
                continue

            try:
                assert not signalled, "Quit signal received"
                assert series in local.mergestate, "series was not created in local database yet"
                remote.seriesStart(series)
                with DataInterface.connectRemote(server=remote, user=series, password=passwords[series]) as remotedb:
                    remote.updateCacheFrom(remotedb, series)

                    if remote.mergestate[series]['totalhash'] != local.mergestate[series]['totalhash']:
                        log.debug("Need to merge %s:", series)

                        # Obtain a merge lock on both sides and start the merge
                        with DataInterface.mergelocks(local, localdb, remote, remotedb, series):
                            ltables = local.mergestate[series]['hashes']
                            rtables = remote.mergestate[series]['hashes']
                            self.mergeTables(localdb, remotedb, set([k for k in ltables if ltables[k] != rtables[k]]))

                            remotedb.commit()
                            localdb.commit()

                        # Rescan the tables to verify we are at the same state
                        remote.updateCacheFrom(remotedb, series)
                        local.updateCacheFrom(localdb, series)
                        remote.mergestate[series].pop('error', None)

            except Exception as e:
                error = str(e)
                log.warning("Merge with %s/%s failed: %s", remote.hostname, series, e, exc_info=e)

            remote.seriesDone(series, error)
        remote.mergeDone()


    def mergeTables(self, localdb, remotedb, tables):
        count = 0
        for ii in range(5):
            if len(tables) <= 0: return
            tables = self._mergeTablesInternal(localdb, remotedb, tables)
            log.debug("unfinished tables = %s", tables)
        log.error("Ran merge tables 5 times.  Quitting")

    def _mergeTablesInternal(self, localdb, remotedb, tables):
        global signalled
        localinsert = defaultdict(list)
        localupdate = defaultdict(list)
        localdelete = defaultdict(list)
        localundelete = defaultdict(list)

        remoteinsert = defaultdict(list)
        remoteupdate = defaultdict(list)
        remotedelete = defaultdict(list)
        remoteundelete = defaultdict(list)

        for t in tables:
            assert not signalled, "Quit signal received"
            log.debug("{}  collection".format(t))

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
        for t in TABLE_ORDER:
            assert not signalled, "Quit signal received"
            log.debug("%s insert", t)
            DataInterface.insert(localdb,  localinsert[t])
            DataInterface.insert(remotedb, remoteinsert[t])

        # Update/delete order next (bottom up)
        log.debug("Performing updates/deletes")
        for t in reversed(TABLE_ORDER):
            assert not signalled, "Quit signal received"
            log.debug("%s update/delete", t)
            DataInterface.update(localdb,  localupdate[t])
            DataInterface.update(remotedb, remoteupdate[t])

            remoteundelete[t].extend(DataInterface.delete(localdb,  localdelete[t]))
            localundelete[t].extend(DataInterface.delete(remotedb, remotedelete[t]))

        # If we have foreign key violations trying to delete, we need to readd those back to the opposite site and redo the merge
        # The only time this should ever occur is with the drivers table as its shared between series
        unfinished = set()
        for t in remoteundelete:
            if len(remoteundelete[t]) > 0:
                unfinished.add(t)
                DataInterface.insert(remotedb, remoteundelete[t])
        for t in localundelete:
            if len(localundelete[t]) > 0:
                unfinished.add(t)
                DataInterface.insert(localdb, localundelete[t])

        return unfinished

