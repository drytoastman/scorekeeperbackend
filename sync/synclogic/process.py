#!/usr/bin/env python3

import base64
from collections import defaultdict
import datetime
import logging
import os
import psycopg2
import psycopg2.extras
import queue
import signal
import threading
import time
from types import SimpleNamespace
import uuid

from synclogic.mergeserver import MergeServer
from synclogic.model import DataInterface
from synclogic.exceptions import *
from synclogic.objects import *

log  = logging.getLogger(__name__)

class CheckInterference(threading.Thread):
    """
        When doing lengthy operations:
            - make sure that the opposite database doesn't hit its idle_in_transaction_timeout
            - make sure a long running operation holding locks is holding up real users like DataEntry or Registration
    """
    def __init__(self, db):
        threading.Thread.__init__(self, daemon=True)
        self.db = db
        self.done = False
        self.change(False)

    def change(self, isactive):
        self.active = isactive
        self.blocks = dict()
        self.nextcheck = time.time() + 0.5

    def run(self):
        while not self.done:
            if time.time() >= self.nextcheck:
                if not self.active:
                    self.check()
                self.nextcheck = time.time() + 0.5
            time.sleep(max(0.1, self.nextcheck - time.time()))
        log.debug("Interference thread done")

    def check(self):
        with self.db.cursor() as cur:
            # Find all blocked pids that are are the cause of, also resets the idle_in_transaction timer
            cur.execute("SELECT application_name,query_start,pid from pg_stat_activity where wait_event_type='Lock' and datname='scorekeeper' and pg_backend_pid()=ANY(pg_blocking_pids(pid))")
            for row in cur.fetchall():
                (name,start,pid) = row

                cur = self.blocks.get(pid, SimpleNamespace(start=0))
                if cur.start != start: # not the same blocked query
                    self.blocks[pid] = SimpleNamespace(start=start, mark=time.time())
                    continue

                # We are still blocking this, abort now
                span = time.time() - cur.mark
                if (name.lower() in ('dataentry', 'registration') and span > 3.0) or (name.lower() in ('webserver') and span > 5.0):
                    log.warning("Aborting database connection %s as we are blocking %s", self.db.dsn, name)
                    self.db.close()
                    self.done = True


class DBWatcher(threading.Thread):
    """
        When doing lengthy operations:
            - make sure postgres client connection isn't hung on a dead network connection
            - start/control the interference watchers as well
    """
    def __init__(self, localdb, remotedb):
        threading.Thread.__init__(self, daemon=True)
        self.localintf  = CheckInterference(localdb)
        self.remoteintf = CheckInterference(remotedb)
        self.done = False
        self.off()

    def run(self):
        self.localintf.start()
        self.remoteintf.start()
        while not self.done:
            time.sleep(0.5)
            now = time.time()
            localtime  = self.localstart and (now - self.localstart) or 0
            remotetime = self.remotestart and (now - self.remotestart) or 0
            if localtime > 30 or remotetime > 30:
                log.warning("Aborting sync as an operation has taken more than 30 seconds (%s, %s)", localtime, remotetime)
                self.stop()
                os.close(self.localintf.db.fileno())
                os.close(self.remoteintf.db.fileno())
                os.kill(os.getpid(), signal.SIGHUP)

    def local(self):
        self.localintf.change(True)
        self.remoteintf.change(False)
        self.localstart = time.time()
        self.remotestart = None

    def remote(self):
        self.localintf.change(False)
        self.remoteintf.change(True)
        self.localstart = None
        self.remotestart = time.time()

    def off(self):
        self.localintf.change(False)
        self.remoteintf.change(False)
        self.localstart = None
        self.remotestart = None

    def stop(self):
        self.done = True
        self.localintf.done = True
        self.remoteintf.done = True


class MergeProcess():

    def __init__(self, args):
        psycopg2.extras.register_uuid()
        self.wakequeue = queue.Queue()
        self.signalled = False
        self.done = False
        self.listener = None
        self.useport = -1
        if len(args):
            self.useport = int(args[0])

    def shutdown(self):
        """ Interrupt what we are doing and quit """
        self.signalled = True
        self.wakequeue.put(True)

    def poke(self):
        """ Just wake the queue wait, don't interrupt current work """
        self.wakequeue.put(False)

    def qwait(self, timeout):
        # Wait for timeout seconds.  Wake immediately if something is dropped in the queue.
        try:
            self.done = self.wakequeue.get(timeout=timeout)
        except:
            pass

    def runforever(self):
        while not self.done:
            try:
                DataInterface.initialize(self.useport)
                log.info("Sync DB models initialized")
                break
            except Exception as e:
                log.info("Error during model initialization, waiting for db and template: %s", e)
            self.qwait(2)

        while not self.done:
            self.runonce()
            self.qwait(10)

    def runonce(self):
        try:
            with DataInterface.connectLocal(self.useport) as localdb:
                # Reset our world on each loop
                me = MergeServer.getLocal(localdb)
                passwords = DataInterface.loadPasswords(localdb)

                # Check for any quickruns flags and do those first
                for remote in MergeServer.getQuickRuns(localdb):
                    log.debug("quickrun {}".format(remote.hostname))
                    self.mergeRuns(localdb, me, remote, passwords)

                me.updateSeriesFrom(localdb)
                for series in me.mergestate.keys():
                    me.updateCacheFrom(localdb, series)


                # Check if there are any timeouts for servers to merge with
                for remote in MergeServer.getActive(localdb):
                    if remote.nextcheck < datetime.datetime.utcnow():
                        try:
                            remote.serverStart(me.mergestate.keys())
                            self.mergeWith(localdb, me, remote, passwords)
                            remote.serverDone()
                        except Exception as e:
                            log.error("Caught exception merging with {}: {}".format(remote, e), exc_info=e)
                            with DataInterface.connectLocal(self.useport) as localdb2:  # local db conn may be bad at this point
                                remote.serverError(localdb2, str(e))

                # Don't hang out in idle transaction from selects
                try: localdb.rollback()
                except: pass

        except (NoDatabaseException, NoLocalHostServer) as ie:
            log.debug(type(ie).__name__)

        except Exception as e:
            log.error("Caught exception in main loop: {}".format(e), exc_info=e)



    def mergeRuns(self, localdb, local, remote, passwords):
        try:
            error  = None
            series = remote.quickruns
            if series not in passwords:
                return

            remote.runsStart(series)
            with DataInterface.connectRemote(server=remote, user=series, password=passwords[series]) as remotedb:
                with DataInterface.mergelocks(local, localdb, remote, remotedb, series):
                    self.mergeTables(remote, series, localdb, remotedb, set(['runs']))
                    remotedb.commit()
                    localdb.commit()
                remote.updateCacheFrom(remotedb, series)
                local.updateCacheFrom(localdb, series)

        except Exception as e:
            error = str(e)
            log.warning("Quick runs with %s/%s failed: %s", remote.hostname, series, e, exc_info=e)

        finally:
            remote.runsDone(series, error)




    def mergeWith(self, localdb, local, remote, passwords):
        """ Run a merge process with the specified remote server """
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
                assert not self.signalled, "Quit signal received"
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
        try:
            count = 0
            watcher = DBWatcher(localdb, remotedb)
            watcher.start()
            for ii in range(5):
                if len(tables) <= 0:
                    break
                tables = self._mergeTablesInternal(remote, series, localdb, remotedb, tables, watcher)
                if tables:
                    log.warning("unfinished tables = %s", tables)
            else:
                log.error("Ran merge tables 5 times and not complete.")
        finally:
            if watcher:
                watcher.stop()


    def _mergeTablesInternal(self, remote, series, localdb, remotedb, tables, watcher):
        """ The core function for actually finding the real differences and applying them locally or remotely """
        localinsert = defaultdict(list)
        localupdate = defaultdict(list)
        localdelete = defaultdict(list)
        localundelete = defaultdict(list)

        remoteinsert = defaultdict(list)
        remoteupdate = defaultdict(list)
        remotedelete = defaultdict(list)
        remoteundelete = defaultdict(list)

        for t in tables:
            assert not self.signalled, "Quit signal received"
            remote.seriesStatus(series, "Analysis {}".format(t))
            self.listener and self.listener("analysis", t, localdb, remotedb, watcher)

            # Load data from both databases, load it all in one go to be more efficient in updates later
            watcher.local()
            localobj  = PresentObject.loadPresent(localdb, t)
            watcher.remote()
            remoteobj = PresentObject.loadPresent(remotedb, t)
            watcher.off()

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
            watcher.local()
            ldeleted = DeletedObject.deletedSince( localdb, t,  PresentObject.minmodtime(remoteobj))
            watcher.remote()
            rdeleted = DeletedObject.deletedSince(remotedb, t,  PresentObject.minmodtime(localobj))
            watcher.off()

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
            assert not self.signalled, "Quit signal received"
            remote.seriesStatus(series, "Insert {}".format(t))
            self.listener and self.listener("insert", t, localdb, remotedb, watcher)

            watcher.local()
            if not DataInterface.insert(localdb,  localinsert[t]):
                unfinished.add(t)
            watcher.remote()
            if not DataInterface.insert(remotedb, remoteinsert[t]):
                unfinished.add(t)
            watcher.off()


        # Update/delete order next (bottom up)
        log.debug("Performing updates/deletes")
        for t in reversed(DataInterface.TABLE_ORDER):
            assert not self.signalled, "Quit signal received"
            remote.seriesStatus(series, "Update {}".format(t))
            self.listener and self.listener("update", t, localdb, remotedb, watcher)

            if t in DataInterface.ADVANCED_TABLES:
                self.advancedMerge(localdb, remotedb, t, localupdate[t], remoteupdate[t], watcher)
            else:
                watcher.local()
                if not DataInterface.update(localdb,  localupdate[t]):
                    unfinished.add(t)
                watcher.remote()
                if not DataInterface.update(remotedb, remoteupdate[t]):
                    unfinished.add(t)
                watcher.off()

            remote.seriesStatus(series, "Delete {}".format(t))
            self.listener and self.listener("delete", t, localdb, remotedb, watcher)
            remoteundelete[t].extend(DataInterface.delete(localdb,  localdelete[t]))
            localundelete[t].extend(DataInterface.delete(remotedb, remotedelete[t]))

        # If we have foreign key violations trying to delete, we need to readd those back to the opposite site and redo the merge
        # The only time this should ever occur is with the drivers table as its shared between series
        for t in remoteundelete:
            if len(remoteundelete[t]) > 0:
                log.warning("Remote undelete requests for {}: {}".format(t, len(remoteundelete[t])))
                remote.seriesStatus(series, "R-undelete {}".format(t))
                unfinished.add(t)
                DataInterface.insert(remotedb, remoteundelete[t])
        for t in localundelete:
            if len(localundelete[t]) > 0:
                log.warning("Local udelete requests for {}: {}".format(t, len(remoteundelete[t])))
                remote.seriesStatus(series, "L-undelete {}".format(t))
                unfinished.add(t)
                DataInterface.insert(localdb, localundelete[t])

        return unfinished


    def advancedMerge(self, localdb, remotedb, table, remoteobj, localobj, watcher):
        when   = PresentObject.mincreatetime(localobj, remoteobj)
        local  = { l.pk:l for l in localobj  }
        remote = { r.pk:r for r in remoteobj }
        pkset  = local.keys() | remote.keys()

        loggedobj = dict()
        logtable  = DataInterface.logtablefor(table)

        watcher.local()
        LoggedObject.loadFrom(loggedobj, localdb,  pkset, logtable, table, when)
        watcher.remote()
        LoggedObject.loadFrom(loggedobj, remotedb, pkset, logtable, table, when)
        watcher.off()

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

        watcher.local()
        DataInterface.update(localdb, toupdatel)
        watcher.remote()
        DataInterface.update(remotedb, toupdater)
        watcher.off()

