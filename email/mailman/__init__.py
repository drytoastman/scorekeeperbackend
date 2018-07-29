import logging
import sys
import psycopg2
import psycopg2.extras
from sccommon.logging import logging_setup
import signal
import time

from .sender import SenderThread
from .receiver import ReceiverThread

log = logging.getLogger("mailman.main")

def main():
    logging_setup('/var/log/scemail.log')
    log.info("starting main")

    psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)
    cargs = {
      "cursor_factory": psycopg2.extras.DictCursor,
                "host": "/var/run/postgresql",
                "user": "localuser",
              "dbname": "scorekeeper",
    "application_name": "mailman"
    }
    if len(sys.argv) > 1:  # testing only
        cargs.update({"host": "127.0.0.1", "port": int(sys.argv[1])})

    sender = SenderThread(cargs)
    receiver = ReceiverThread(cargs)
    done = False

    def interrupt(signum, frame):
        log.info("Received signal {}".format(signum))
        nonlocal done, sender, receiver
        if signum == signal.SIGHUP:
            receiver.poke()
        else:
            sender.shutdown()
            receiver.shutdown()
            done = True

    signal.signal(signal.SIGABRT, interrupt)
    signal.signal(signal.SIGINT,  interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGHUP,  interrupt)

    sender.start()
    receiver.start()
    while not done:
        time.sleep(1)
    log.info("exiting main")
