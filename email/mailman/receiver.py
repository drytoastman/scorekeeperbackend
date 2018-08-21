#!/usr/bin/env python3

import email
import imaplib
import logging
import os
import psycopg2
from sccommon.queuesleep import QueueSleepMixin
import time
import threading

log = logging.getLogger(__name__)


class RHeader():
    def __init__(self, headers, name):
        self.name = name
        data = [""]
        for k in headers:
            if k.lower() == name.lower():
                data = [i.strip() for i in headers.get(k).split(';')]
                break

        if len(data) > 1:
            self.ctype = data[0]
            self.data = data[1]
        else:
            self.ctype = None
            self.data = data[0]

        self.data = self.data.replace('\n', '')

    def __repr__(self):
        return "H({}, {})".format(self.name, self.data)


class ReceiverThread(threading.Thread, QueueSleepMixin):

    def __init__(self, cargs):
        threading.Thread.__init__(self)
        QueueSleepMixin.__init__(self)
        self.server   = os.environ['MAIL_RECEIVE_HOST']
        self.user     = os.environ['MAIL_RECEIVE_USER']
        self.password = os.environ['MAIL_RECEIVE_PASS']
        self.cargs    = cargs
 
    def run(self):
        self.done = False
        while not self.done:
            try:
                with imaplib.IMAP4_SSL(self.server) as imap:
                    imap.login(self.user, self.password)
                    imap.select()
                    resp, data = imap.search(None, 'ALL')
                    for num in data[0].split():
                        try:
                            resp, data = imap.fetch(num, '(BODY[])')
                            self.process_message(data[0][1])
                            imap.store(num, '+FLAGS', '\\Deleted')
                        except Exception as e:
                            log.exception("Error processesing message")
                    imap.close()
            except Exception as e:
                log.exception("Error receiving message")

            self.qwait(10)

    def process_message(self, text):
        msg     = email.message_from_bytes(text)
        log.debug("Processing message from {}".format(msg['From']))
        headers = dict()
        for p in msg.get_payload():
            if p.get_content_type() == 'message/delivery-status':
                for d in p.get_payload():
                    headers.update(d)
        
                action = RHeader(headers, 'Action')
                if action.data.lower() != 'delivered':
                    self.process_failure(headers)

    def process_failure(self, headers):
        orig   = RHeader(headers, 'Original-Recipient')
        #final  = RHeader(headers, 'Final-Recipient')
        #date   = RHeader(headers, 'Arrival-Date')
        mta    = RHeader(headers, 'Reporting-MTA')
        rmta   = RHeader(headers, 'Remote-MTA')
        status = RHeader(headers, 'Status')
        #code   = RHeader(headers, 'Diagnostic-Code')

        log.warning("Failure report for:")
        log.warning("\t{}".format(orig))
        log.warning("\t{}".format(mta))
        log.warning("\t{}".format(rmta))
        log.warning("\t{}".format(status))

        with psycopg2.connect(**self.cargs) as db:
            with db.cursor() as cur:
                cur.execute("INSERT INTO emailfailures (email, status) VALUES (%s,%s)", (orig, status))

