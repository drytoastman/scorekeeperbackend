#!/usr/bin/env python3

import base64
import logging
import psycopg2
import psycopg2.extras
import queue
import time
import uuid

import synclogic.model as model

log  = logging.getLogger(__name__)

class MergeProcess():

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
                with model.connectLocal() as db:
                    self.processActiveServers(db)
                    db.rollback()
                    done = self.wakequeue.get(timeout=10)
            except queue.Empty:
                pass
            except Exception as e:
                # Pause to avoid out of control loops
                log.error("Caught exception in main loop {}".format(e), exc_info=e)
                try: done = self.wakequeue.get(timeout=10)
                except: pass
                
    def processActiveServers(self, localdb):
        # If we have the greater serverid, we should be doing the work
        # Still fall back and try a merge ourselves if the other person is delayed
        myid = model.getLocalServerId(localdb)
        log.info("I am {}".format(myid))

        for remoteid in model.getActiveServerIds(localdb):
            checkintvl  = (myid > remoteid and 2 or 1) * 10
            lastcheck   = model.getServerInfo(localdb, remoteid)['mergestate'].get('lastcheck', 0)
            timeleft    = (lastcheck + checkintvl) - time.time()
            log.debug("check {}, last {}, left {}".format(checkintvl, lastcheck, timeleft))

            if timeleft < 0:
                self.mergeWith(localdb, remoteid)
                model.updateServerState(localdb, remoteid, lastcheck = int(time.time()))

    def getSeriesOnServer(self, remoteinfo):
        address = remoteinfo['address'] or remoteinfo['name']
        with model.connectRemote(host=address, user='nulluser', password='nulluser') as remotedb:
            return model.getSeriesList(remotedb)
 
    def mergeWithHost(self, hostname):
        self.mergeWith(uuid.uuid5(uuid.NAMESPACE_DNS, hostname))

    def mergeWith(self, localdb, remoteid):
        remoteinfo  = model.getServerInfo(localdb, remoteid)
        remotestate = remoteinfo['mergestate']
        serieslist  = self.getSeriesOnServer(remoteinfo)

        log.debug("merging with {} {}".format(remoteinfo['serverid'], serieslist))
        for series in serieslist:
            seriesstate = remotestate.get(series, {})
            seriesstate['lastmerge'] = int(time.time())
            model.setSeries(localdb, series)
            lhashes = model.loadHashes(localdb)
            rhashes = model.loadHashes(remotedb)
            seriesstate['hash'] = hashes
            model.updateServerState(localdb, remoteid, **{series:seriesstate})

        #model.updateServerState(remotedb, serverid, remotestate)
            
        # do merge here
        # if connect timeout, mark as inactive?
        #log.info("remote has {}".format(self.getRemoteInfo('scorekeeper.wwscc.org'))) #info['address'])

    def XXmergeWith(self, remoteaddress, series):
            mirror = m.getserver(conn, me['attr']['serverid'])
            mirror['lastmerge'] = int(time.time())
            m.updateserver(conn, mirror)

            remote['lastmerge'] = int(time.time())
            m.updateserver(self.localdb, remote)

            conn.commit()
            conn.close()

            self.localdb.commit()

