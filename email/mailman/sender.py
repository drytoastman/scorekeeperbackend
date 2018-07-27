from bs4 import BeautifulSoup
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText
import email.policy
from email.utils import formataddr, formatdate, make_msgid, parseaddr
import logging
import os
import psycopg2
import smtplib
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


class SenderThread(threading.Thread):

    def __init__(self, cargs):
        threading.Thread.__init__(self)
        self.server  = os.environ['MAIL_SERVER']
        self.sender  = os.environ['MAIL_DEFAULT_SENDER']
        self.replyto = os.environ['MAIL_DEFAULT_REPLYTO']
        self.domain  = self.sender.split('@')[1]
        self.cargs   = cargs

    def run(self):
        self.done = False
        while not self.done:
            try:
                with psycopg2.connect(**self.cargs) as db:
                    with db.cursor() as cur:
                        cur.execute("SELECT * FROM emailqueue ORDER BY created LIMIT 1")
                        if cur.rowcount == 1:
                            row = cur.fetchone()
                            self.process_message(row['content'])
            except Exception as e:
                log.exception("Error in sender: {}".format(e))
            time.sleep(10)

    def process_message(self, request):
        with smtplib.SMTP("") as smtp:
            html = request['body']
            text = BeautifulSoup(html, "lxml").get_text().encode('utf-8').decode('us-ascii', 'ignore')

            msg      = MIMEMultipart(policy=email.policy.SMTP)
            alt      = MIMEMultipart('alternative')
            textbody = MIMEText("", 'plain')
            htmlbody = MIMEText("", 'html')

            alt.attach(textbody)
            alt.attach(htmlbody)
            msg.attach(alt)
            for attach in request.get('attachments', []):
                msg.attach(Base64EncodedFile(attach['data'], attach['mime'], attach['name']))

            msg['From']    = formataddr(parseaddr(self.sender))
            msg['ReplyTo'] = formataddr(parseaddr(request.get('replyto', self.replyto)))
            msg['Subject'] = request['subject'].strip('\n')
            msg['Date']    = formatdate()

            for rcpt in request['recipients']:
                try:
                    del msg['Message-ID'], msg['To']
                    msg['Message-ID'] = make_msgid(domain=self.domain)
                    msg['To']         = formataddr(("{} {}".format(rcpt['firstname'], rcpt['lastname']), rcpt['email']))
                    name              = "{} {}".format(rcpt['firstname'], rcpt['lastname'])
                    htmlbody.set_payload(html.replace('{{NAME}}', name))
                    textbody.set_payload(text.replace('{{NAME}}', name))
                    print(msg)
                    #smtp.send_message(msg)
                except Exception as e:
                    log.exception("Send error: %s", e)

