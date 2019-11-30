import logging
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

    resolver = ScorekeeperResolver()
    udp_server = DNSServer(resolver, logger=ToPyLogger(log))
    udp_server.start()
