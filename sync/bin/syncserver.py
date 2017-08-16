#!/usr/bin/env python3

import copy
import signal
import logging
import synclogic
import queue
import time
import threading

log = logging.getLogger(__name__)

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s %(message)s')
    log.info("starting")

    class ProtectedData():
        def __init__(self):
            self.lock = threading.RLock()
            self.data = {}
        def __enter__(self):
            self.lock.acquire()
            return self.data
        def __exit__(self, etype, evalue, etraceback):
            self.lock.release()

    inqueue = queue.Queue()
    wrappedstate = ProtectedData()
    with wrappedstate as obj:
        obj['z'] = 99

    frontend = synclogic.frontend.FrontendThread(wrappedstate, inqueue)
    frontend.start()

    done = False;
    def shutdown(signum, frame):
        global done
        log.info("stopping server")
        if frontend:
            frontend.stop()
            done = True

    signal.signal(signal.SIGABRT, shutdown)
    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while not done:
        try:
            log.info("obj = {}".format(inqueue.get_nowait()))
        except queue.Empty:
            pass
        time.sleep(0.5)
        with wrappedstate as obj:
            obj['time'] = time.time()
        
    log.info("exiting main")
