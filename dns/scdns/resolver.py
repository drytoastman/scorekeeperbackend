import json
import logging
import psycopg2

from dnslib import A, QTYPE, RCODE, RR, TXT
from dnslib.server import DNSServer, DNSHandler, BaseResolver

log = logging.getLogger(__name__)

class ResolverException(Exception): pass
class NoDatabaseException(ResolverException): pass
class NoNeighborsException(ResolverException): pass

class ScorekeeperResolver(BaseResolver):
    def __init__(self):
        self.db = None

    def resolve(self,request,handler):
        reply = request.reply()
        try:
            if request.q.qtype == QTYPE.A:
                reply.add_answer(RR(request.q.qname, QTYPE.A, ttl=60, rdata=A(self._getmatch(request))))
            else:
                reply.header.rcode = RCODE.NXDOMAIN

        except NoNeighborsException:
            reply.header.rcode = RCODE.NXDOMAIN

        except Exception as e:
            reply.header.rcode = RCODE.SERVFAIL
            log.warning(e)

        return reply

    def _getmatch(self, request):
        h1 = request.q.qname.label[0].decode()
        if not h1 in ('de', 'reg'):
            raise NoNeighborsException()

        if self.db is None: 
            try:
                self.db = psycopg2.connect(user="localuser", dbname="scorekeeper", application_name="dnsserver")
            except Exception as e:
                self.db = None
                raise NoDatabaseException()

        with self.db.cursor() as cur:
            cur.execute("SELECT data FROM localcache WHERE name='neighbors'")
            if cur.rowcount == 1:
                neighbors = json.loads(cur.fetchone()[0])
                for ip, services in neighbors.items():
                    if h1 == 'de'  and 'DATAENTRY' in services:    return ip
                    if h1 == 'reg' and 'REGISTRATION' in services: return ip
                if len(neighbors):
                    # default to first IP, hope for the best
                    return next(iter(neighbors.keys()))

            raise NoNeighborsException()
