import logging
import signal
import sys
import time
import threading

from sccommon.logging import logging_setup
from synclogic.process import MergeProcess

def main():
    logging_setup('/var/log/scsync.log')
    log = logging.getLogger(__name__)
    log.info("starting main")
    mp = MergeProcess(sys.argv[1:])
    done = False

    def interrupt(signum, frame):
        log.info("Received signal {}".format(signum))
        nonlocal mp, done
        if signum == signal.SIGHUP:
            mp.poke()
        else:
            mp.shutdown()
            done = True

    signal.signal(signal.SIGABRT, interrupt)
    signal.signal(signal.SIGINT,  interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGHUP,  interrupt)

    t = threading.Thread(target=mp.runforever)
    t.start()
    while not done:
        time.sleep(1)
    log.info("exiting main")
