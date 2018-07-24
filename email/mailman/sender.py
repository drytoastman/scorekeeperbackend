
from bs4 import BeautifulSoup
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid, parseaddr
import os
import smtplib
import time
import threading

import psycopg2
import psycopg2.extras

psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)


def connect_db(port=-1):
    args = {
      "cursor_factory": psycopg2.extras.DictCursor,
                "host": "/var/run/postgresql",
                "user": "localuser",
              "dbname": "scorekeeper",
    "application_name": "mailman"
    }
    if port > 0:
        args.update({"host": "127.0.0.1", "port": port})
    return psycopg2.connect(**args)


class Base64EncodedFile(EmailMessage):
    def __init__(self, base64data, mimetype, filename):
        EmailMessage.__init__(self)
        self.set_payload(base64data)
        self['Content-Type']              = '{}; name="{}"'.format(mimetype, filename)
        self['MIME-Version']              = '1.0'
        self['Content-Transfer-Encoding'] = 'base64'
        self['Content-Disposition']       = 'attachment; filename="{}"'.format(filename)


class SenderThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.server  = os.environ.get('MAIL_SERVER', None)
        self.sender  = os.environ.get('MAIL_DEFAULT_SENDER', None)
        self.replyto = os.environ.get('MAIL_DEFAULT_REPLYTO', None)
        self.domain  = self.sender.split('@')[1]
 
    def run(self):
        self.done = False
        self.db = connect_db(6432)
        while not self.done:
            with self.db.cursor() as cur:
                cur.execute("SELECT * FROM emailqueue ORDER BY created LIMIT 1")
                if cur.rowcount == 1:
                    row = cur.fetchone()
                    self.process_message(row['content'])
            time.sleep(10)

    def process_message(self, request):
        with smtplib.SMTP("") as smtp:
            msg = MIMEMultipart()
            alternative = MIMEMultipart('alternative')
            alternative.attach(MIMEText(BeautifulSoup(request['body']).get_text(), 'plain'))
            alternative.attach(MIMEText(request['body'], 'html'))
            msg.attach(alternative)

            msg['From']    = formataddr(parseaddr(self.sender))
            msg['ReplyTo'] = formataddr(parseaddr(request.get('replyto', self.replyto)))
            msg['Subject'] = request['subject'].strip('\n')
            msg['Date']    = formatdate()

            #attachments.append({'name': d.filename, 'mime': d.mimetype, 'data': base64.b64encode(data).decode() })
            for attach in request.get('attachments', []):
                msg.attach(Base64EncodedFile(attach['data'], attach['mime'], attach['name']))

            for rcpt in request['recipients']:
                try:
                    del msg['Message-ID'], msg['To']
                    msg['Message-ID'] = make_msgid(domain=self.domain)
                    msg['To'] = formataddr(("{} {}".format(rcpt['firstname'], rcpt['lastname']), rcpt['email']))
                    print("send \n{}".format(msg))
                except Exception as e:
                    log.exception("Send error: %s", e)

        """
        if self.subject:
            msg['Subject'] = sanitize_subject(force_text(self.subject), encoding)

        msg['From'] = sanitize_address(self.sender, encoding)
        msg['To'] = ', '.join(list(set(sanitize_addresses(self.recipients, encoding))))

        """


