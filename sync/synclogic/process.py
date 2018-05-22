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

from synclogic.mergeserver import MergeServer
from synclogic.model import DataInterface
from synclogic.exceptions import *
from synclogic.objects import *

log  = logging.getLogger(__name__)
signalled = False

class SkipThisRound(Exception):
    pass

class MergeProcess():

    def __init__(self, args):
        psycopg2.extras.register_uuid()
        self.wakequeue = queue.Queue()
        self.useport = -1
        if len(args):
            self.useport = int(args[0])

    def shutdown(self):
        """ Interrupt what we are doing and quit """
        global signalled
        signalled = True
        self.wakequeue.put(True)

    def poke(self):
        """ Just wake the queue wait, don't interrupt current work """
        self.wakequeue.put(False)

    def runforever(self):
        global signalled
        done = False

        while not done:
            try:
                DataInterface.initialize(self.useport)
                break
            except Exception as e:
                log.info("Error during model initialization, waiting for db and template: %s", e)

            try: done = self.wakequeue.get(timeout=2)
            except: pass

        log.info("Sync DB models initialized")

        while not done:
            self.runonce()
            # Wait for 10 seconds before rescanning.  Wake immediately if something is dropped in the queue
            try: done = self.wakequeue.get(timeout=10)
            except: pass


    def runonce(self):
        try:
            signalled = False
            with DataInterface.connectLocal(self.useport) as localdb:
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
                            remote.serverStart(me.mergestate.keys())
                            self.mergeWith(localdb, me, remote, passwords)
                            remote.serverDone()
                        except Exception as e:
                            log.error("Caught exception merging with {}: {}".format(remote, e), exc_info=e)
                            remote.serverError(str(e))

                # Don't hang out in idle transaction from selects
                localdb.rollback()

        except (NoDatabaseException, NoLocalHostServer) as ie:
            log.debug(type(ie).__name__)

        except Exception as e:
            log.error("Caught exception in main loop: {}".format(e), exc_info=e)



    def mergeWith(self, localdb, local, remote, passwords):
        """ Run a merge process with the specified remote server """
        global signalled

        # First connect to the remote server with nulluser just to update the list of active series
        log.debug("checking %s", remote)
        with DataInterface.connectRemote(server=remote, user='nulluser', password='nulluser') as remotedb:
            remote.updateSeriesFrom(remotedb)

        # Now, for each active series in the remote database, check if we have the password to connect
        for series in remote.mergestate.keys():
            error = None
            if series not in passwords:
                remote.seriesDone(series, "No password for %s, skipping" % (series,))
                continue

            try:
                assert not signalled, "Quit signal received"
                assert series in local.mergestate, "series was not created in local database yet"

                # Mark this series as the one we are actively merging with remote and make the series/password connection
                remote.seriesStart(series)
                with DataInterface.connectRemote(server=remote, user=series, password=passwords[series]) as remotedb:
                    remote.updateCacheFrom(remotedb, series)

                    # If the totalhash of our local copy differs from the remote copy, we need to actually do something
                    if remote.mergestate[series]['totalhash'] != local.mergestate[series]['totalhash']:
                        log.debug("Need to merge %s:", series)

                        # Obtain a merge lock on both sides, find which tables different and run mergeTables()
                        with DataInterface.mergelocks(local, localdb, remote, remotedb, series):
                            ltables = local.mergestate[series]['hashes']
                            rtables = remote.mergestate[series]['hashes']
                            self.mergeTables(remote, series, localdb, remotedb, set([k for k in ltables if ltables[k] != rtables[k]]))
                            remote.seriesStatus(series, "Commit Changes")
                            remotedb.commit()
                            localdb.commit()

                        # Rescan the tables to verify we are at the same state
                        remote.updateCacheFrom(remotedb, series)
                        local.updateCacheFrom(localdb, series)
                        remote.mergestate[series].pop('error', None)

            except Exception as e:
                error = str(e)
                log.warning("Merge with %s/%s failed: %s", remote.hostname, series, e, exc_info=e)

            finally:
                remote.seriesDone(series, error)





    def mergeTables(self, remote, series, localdb, remotedb, tables):
        """ Outer loop to rerun mergeTables if for some reason, we are still not totally up to date after running """
        count = 0
        for ii in range(5):
            if len(tables) <= 0: return
            tables = self._mergeTablesInternal(remote, series, localdb, remotedb, tables)
            log.debug("unfinished tables = %s", tables)
        log.error("Ran merge tables 5 times.  Quitting")


    def _mergeTablesInternal(self, remote, series, localdb, remotedb, tables):
        """ The core function for actually finding the real differences and applying them locally or remotely """
        global signalled
        localinsert = defaultdict(list)
        localupdate = defaultdict(list)
        localdelete = defaultdict(list)
        localundelete = defaultdict(list)

        remoteinsert = defaultdict(list)
        remoteupdate = defaultdict(list)
        remotedelete = defaultdict(list)
        remoteundelete = defaultdict(list)

        nextping = 0
        def seriesStatus(msg):
            """
              Update series status, also take time to check for quit signal and ping remote server to stop
              idle_in_transaction timeout during long amounts of time inserting/updating data into the local
              database.  We do rate limit it a bit though as remote calls are slow across the Internet
            """
            nonlocal nextping
            assert not signalled, "Quit signal received"
            remote.seriesStatus(series, msg)
            now = time.time()
            if now > nextping:
                with remotedb.cursor() as cur:
                    log.debug("PING remote at %s", now)
                    cur.execute("select 1")
                    nextping = now + 0.5


        for t in tables:
            seriesStatus("Analysis {}".format(t))

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
        unfinished = set()

        # Insert order first (top down)
        for t in DataInterface.TABLE_ORDER:
            seriesStatus("Insert {}".format(t))

            if not DataInterface.insert(localdb,  localinsert[t]):
                unfinished.add(t)
            if not DataInterface.insert(remotedb, remoteinsert[t]):
                unfinished.add(t)

        # Update/delete order next (bottom up)
        log.debug("Performing updates/deletes")
        for t in reversed(DataInterface.TABLE_ORDER):
            seriesStatus("Update {}".format(t))

            if t in DataInterface.ADVANCED_TABLES:
                self.advancedMerge(localdb, remotedb, t, localupdate[t], remoteupdate[t])
            else:
                if not DataInterface.update(localdb,  localupdate[t]):
                    unfinished.add(t)
                if not DataInterface.update(remotedb, remoteupdate[t]):
                    unfinished.add(t)

            seriesStatus("Delete {}".format(t))
            remoteundelete[t].extend(DataInterface.delete(localdb,  localdelete[t]))
            localundelete[t].extend(DataInterface.delete(remotedb, remotedelete[t]))

        # If we have foreign key violations trying to delete, we need to readd those back to the opposite site and redo the merge
        # The only time this should ever occur is with the drivers table as its shared between series
        for t in remoteundelete:
            if len(remoteundelete[t]) > 0:
                log.warning("Remote undelete requests for {}: {}".format(t, len(remoteundelete[t])))
                seriesStatus("R-undelete {}".format(t))
                unfinished.add(t)
                DataInterface.insert(remotedb, remoteundelete[t])
        for t in localundelete:
            if len(localundelete[t]) > 0:
                log.warning("Local udelete requests for {}: {}".format(t, len(remoteundelete[t])))
                seriesStatus("L-undelete {}".format(t))
                unfinished.add(t)
                DataInterface.insert(localdb, localundelete[t])

        return unfinished


    def advancedMerge(self, localdb, remotedb, table, remoteobj, localobj):
        when   = PresentObject.mincreatetime(localobj, remoteobj)
        local  = { l.pk:l for l in localobj  }
        remote = { r.pk:r for r in remoteobj }
        pkset  = local.keys() | remote.keys()

        loggedobj = dict()
        logtable  = DataInterface.logtablefor(table)
        LoggedObject.loadFrom(loggedobj, localdb,  pkset, logtable, table, when)
        LoggedObject.loadFrom(loggedobj, remotedb, pkset, logtable, table, when)

        # Create update objects and then update where needed
        toupdatel = []
        toupdater = []
        for lo in loggedobj.values():
            if not lo:
                continue
            if lo.pk in local:
                update,both = lo.finalize(local[lo.pk])
                toupdater.append(update)
                if both: toupdatel.append(update)
            else:
                update,both = lo.finalize(remote[lo.pk])
                toupdatel.append(update)
                if both: toupdater.append(update)

        DataInterface.update(localdb, toupdatel)
        DataInterface.update(remotedb, toupdater)

