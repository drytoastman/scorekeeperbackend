import logging
import sys
import psycopg2
import psycopg2.extras
from sccommon.logging import logging_setup

from .sender import SenderThread


def main():
    #logging_setup('/var/log/scemail.log')
    logging.basicConfig(level=logging.NOTSET)
    log = logging.getLogger(__name__)
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

    SenderThread(cargs).start()
