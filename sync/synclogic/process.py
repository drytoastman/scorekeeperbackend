#!/usr/bin/env python3

import base64
import logging
import psycopg2
import psycopg2.extras
import queue
import time
import uuid

import synclogic.model as model
from synclogic.model import MergeServer

log  = logging.getLogger(__name__)


def amleader(myid, remoteid):
    return myid < remoteid

class MergeProcess():

    # If we have the greater serverid, I am the leader and should be doing the work
    # Still fall back and try a merge ourselves if the leader isn't doing anything
    LEADER_WAIT = 10
    FOLLOWER_WAIT = 20

    def __init__(self):
        psycopg2.extras.register_uuid()
        self.wakequeue = queue.Queue()

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
                    self.me = MergeServer.getLocal(localdb)
                    log.info("I am {}".format(self.me.serverid))

                    # First merge with anyone the user told us to right away
                    for remote in MergeServer.getNow(localdb):
                        self.mergeWith(localdb, remote)

                    # Then check if there are any timeouts for local servers to merge with
                    for remote in MergeServer.getActive(localdb):
                        timeleft  = (remote.lastcheck.timestamp() + (amleader(self.me.serverid, remote.serverid) and MergeProcess.LEADER_WAIT or MergeProcess.FOLLOWER_WAIT)) - time.time()
                        if timeleft < 0:
                            self.mergeWith(localdb, remote)

                    localdb.rollback() # Don't hang out in idle transaction
                    done = self.wakequeue.get(timeout=10)
            except queue.Empty:
                pass
            except Exception as e:
                # Pause to avoid out of control loops
                log.error("Caught exception in main loop: {}".format(e), exc_info=e)
                try: done = self.wakequeue.get(timeout=10)
                except: pass
                

    def mergeWithHost(self, hostname):
        self.mergeWith(uuid.uuid5(uuid.NAMESPACE_DNS, hostname))

    def mergeWith(self, localdb, remote):
        address = remote.address or remote.hostname
        with model.connectRemote(host=address, user='nulluser', password='nulluser') as remotedb:
            serieslist = model.getSeriesList(remotedb)

        log.debug("merging with {} {}".format(remote.serverid, serieslist))
        for series in serieslist:
            seriesstate = remote.mergestate.setdefault(series, {})
            seriesstate['lastmerge'] = int(time.time())
            model.setSeries(localdb, series)
            lhashes = model.loadHashes(localdb)
            #rhashes = model.loadHashes(remotedb)
            seriesstate['hash'] = lhashes
            remote.update(localdb)

        #model.updateServerState(localdb, remoteid, lastcheck = int(time.time()))
        #model.updateServerState(remotedb, serverid, remote.mergestate)

