import logging
import signal
import sys
import warnings

warnings.filterwarnings("ignore", ".*psycopg2 wheel package will be renamed.*")

from dnslib.server    import DNSServer
from sccommon.logging import logging_setup
from .logger   import ToPyLogger
from .resolver import ScorekeeperResolver

def main():
    logging_setup('/var/log/scdns.log')
    log = logging.getLogger(__name__)
    log.info("starting main")

    def interrupt(signum, frame):
        sys.exit(0)
    signal.signal(signal.SIGABRT, interrupt)
    signal.signal(signal.SIGINT,  interrupt)
    signal.signal(signal.SIGTERM, interrupt)

    tcp_server = DNSServer(resolver=ScorekeeperResolver(), logger=ToPyLogger(log), tcp=True)
    tcp_server.start_thread()

    udp_server = DNSServer(resolver=ScorekeeperResolver(), logger=ToPyLogger(log))
    udp_server.start()
