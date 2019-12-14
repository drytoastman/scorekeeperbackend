
from dnslib import QTYPE, RCODE


class ToPyLogger:
    """ Minimal implementation to output DNS logs to our logging file via normal pythong logging """

    def __init__(self,logger):
        self.logger = logger

    def log_recv(self, handler, data): pass
    def log_send(self, handler, data): pass

    def log_request(self, handler, request):
        self.logger.info("Request: [%s] / '%s' (%s)" % (handler.client_address, request.q.qname, QTYPE[request.q.qtype]))
        self.log_data(request)

    def log_reply(self, handler, reply):
        if reply.header.rcode == RCODE.NOERROR:
            self.logger.info("Reply: %s / '%s' (%s) / RRs: %s" % (handler.client_address, reply.q.qname, QTYPE[reply.q.qtype], ",".join([QTYPE[a.rtype] for a in reply.rr])))
        else:
            self.logger.info("Reply: %s / '%s' (%s) / RRs: %s" % (handler.client_address, reply.q.qname, QTYPE[reply.q.qtype], RCODE[reply.header.rcode]))
        self.log_data(reply)

    def log_truncated(self, handler, reply):
        self.logger.info("Truncated Reply: %s / '%s' (%s) / RRs: %s" % ( handler.client_address, reply.q.qname, QTYPE[reply.q.qtype], ",".join([QTYPE[a.rtype] for a in reply.rr])))
        self.log_data(reply)

    def log_error(self, handler, e):
        self.logger.info("Invalid Request: %s :: %s" % (handler.client_address, e))

    def log_data(self, dnsobj):
        self.logger.debug("\t" + dnsobj.toZone("    "))
