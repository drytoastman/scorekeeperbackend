import logging
import signal
import socket
import sys
import time
import threading

import warnings
warnings.filterwarnings("ignore", ".*psycopg2 wheel package will be renamed.*")

from sccommon.logging  import logging_setup
from synclogic.model   import DataInterface
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


class DumbServer():
    def __init__(self, hostaddr):
        self.address  = socket.gethostbyname(hostaddr)
        self.ctimeout = 10
    def recordConnectFailure(self):
        pass

def remotelist():
    with DataInterface.connectRemote(server=DumbServer(sys.argv[1]), user='nulluser', password='nulluser') as db:
        print(','.join(DataInterface.seriesList(db)))

def remotepassword():
    with DataInterface.connectRemote(server=DumbServer(sys.argv[1]), user=sys.argv[2], password=sys.argv[3]) as db:
        print("accepted")
