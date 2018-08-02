from bs4 import BeautifulSoup
from email import policy
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid, parseaddr
import logging
import os
import psycopg2
import smtplib
from sccommon.queuesleep import QueueSleepMixin
import time
import threading


log = logging.getLogger(__name__)

class Base64EncodedFile(EmailMessage):
    def __init__(self, base64data, mimetype, filename):
        EmailMessage.__init__(self)
        self.set_payload(base64data)
        self['Content-Type']              = '{}; name="{}"'.format(mimetype, filename)
        self['MIME-Version']              = '1.0'
        self['Content-Transfer-Encoding'] = 'base64'
        self['Content-Disposition']       = 'attachment; filename="{}"'.format(filename)


def addUnsub(msg, htmlbody, textbody, html, text, driverid):
    msg['List-Id'] = "some id here"
    msg['List-Unsubscribe'] = "<mailto:unsubscribe-espc-tech-12345N@domain.com>, <http://domain.com/member/unsubscribe/?listname=espc-tech@domain.com?id=12345N>"
    htmlbody.set_payload(html.replace('{{NAME}}', name) + 'some extra stuff here')
    textbody.set_payload(text.replace('{{NAME}}', name) + 'some extra stuff here')

class SenderThread(threading.Thread, QueueSleepMixin):

    def __init__(self, cargs):
        threading.Thread.__init__(self)
        QueueSleepMixin.__init__(self)
        self.server  = os.environ['MAIL_SEND_HOST']
        self.sender  = os.environ['MAIL_SEND_FROM']
        self.replyto = os.environ['MAIL_SEND_DEFAULT_REPLYTO']
        self.domain  = self.sender.split('@')[1]
        self.cargs   = cargs

    def run(self):
        self.done = False
        while not self.done:
            try:
                with psycopg2.connect(**self.cargs) as db:
                    with db.cursor() as cur:
                        while True:
                            cur.execute("SELECT * FROM emailqueue ORDER BY created LIMIT 1")
                            if cur.rowcount == 0:
                                break
                            row = cur.fetchone()
                            log.debug("Processing message %s", row['mailid'])
                            self.process_message(row['content'])
                            break
                            #cur.execute("DELETE FROM emailqueue WHERE mailid=%s", (row['mailid'],))
            except Exception as e:
                log.exception("Error in sender: {}".format(e))

            self.qwait(10)

    def process_message(self, request):
        with smtplib.SMTP(self.server) as smtp:
            unsub = request.get('unsub', False)
            if unsub:
                for r in request['recipients']:

            html = request['body']
            text = BeautifulSoup(html, "lxml").get_text().encode('utf-8').decode('us-ascii', 'ignore')

            msg      = MIMEMultipart(policy=policy.SMTP)
            alt      = MIMEMultipart('alternative')
            textbody = MIMEText("", 'plain')
            htmlbody = MIMEText("", 'html')

            alt.attach(textbody)
            alt.attach(htmlbody)
            msg.attach(alt)
            for attach in request.get('attachments', []):
                msg.attach(Base64EncodedFile(attach['data'], attach['mime'], attach['name']))

            if 'replyto' in request:
                replyto = parseaddr(request['replyto'])
            else:
                replyto = ('Scorekeeper Admin', self.replyto)

            msg['From']     = formataddr(("{} via Mailman".format(replyto[0]), self.sender))
            msg['Reply-To'] = formataddr(replyto)
            msg['Subject']  = request['subject'].strip('\n')
            msg['Date']     = formatdate()

            for rcpt in request['recipients']:
                try:
                    if unsub and 'driverid' not in r:
                        log.warning("Sending email to %s and unsub requested but no driver id present", r['email'])

                    del msg['Message-ID'], msg['To']
                    msg['Message-ID'] = make_msgid(domain=self.domain)
                    msg['To']         = formataddr(("{} {}".format(rcpt['firstname'], rcpt['lastname']), rcpt['email']))
                    name              = "{} {}".format(rcpt['firstname'], rcpt['lastname'])
                    setbody(msg, htmlbody, textbody, html, text)
                    smtp.send_message(msg)
                except Exception as e:
                    log.exception("Send error: %s", e)

