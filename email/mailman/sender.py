from bs4 import BeautifulSoup
from email import encoders
from email import policy
from email.header import Header
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
import urllib.parse


log = logging.getLogger(__name__)
UPLOAD_DIR = '/var/uploads'

class Base64EncodedFile(EmailMessage):
    def __init__(self, mimetype, filename):
        EmailMessage.__init__(self)
        with open(os.path.join(UPLOAD_DIR, filename), 'rb') as fp:
            self.set_payload(fp.read())
        self['MIME-Version']        = '1.0'
        self['Content-Type']        = '{}; name="{}"'.format(mimetype, filename)
        self['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        encoders.encode_base64(self)


class SenderThread(threading.Thread, QueueSleepMixin):

    def __init__(self, cargs):
        threading.Thread.__init__(self)
        QueueSleepMixin.__init__(self)

        try:
            with open(os.environ['SECRETS_FILE'], 'r') as fp:
                secrets       = json.load(fp)
                self.user     = secrets['MAIL_SEND_USER']
                self.password = secrets['MAIL_SEND_PASS']
        except:
            pass

        self.server  = os.environ['MAIL_SEND_HOST']
        self.sender  = os.environ['MAIL_SEND_FROM']
        self.replyto = os.environ['MAIL_SEND_DEFAULT_REPLYTO']
        self.domain  = self.sender.split('@')[1]
        self.policy  = policy.SMTP.clone(max_line_length=300)
        self.cargs   = cargs

    def run(self):
        self.done = False
        while not self.done:
            try:
                with psycopg2.connect(**self.cargs) as db:
                    with db.cursor() as cur:
                        cur.execute("SELECT * FROM emailqueue ORDER BY created LIMIT 20")
                        if cur.rowcount > 0:
                            with smtplib.SMTP(self.server) as smtp:
                                if hasattr(self, 'password'):
                                    smtp.login(self.user, self.password)
                                for row in cur.fetchall():
                                    log.debug("Processing message %s", row['mailid'])
                                    self.process_message(smtp, row['content'])
                                    cur.execute("DELETE FROM emailqueue WHERE mailid=%s", (row['mailid'],))
            except Exception as e:
                log.exception("Error in sender: {}".format(e))

            self.qwait(10)

    def process_message(self, smtp, request):
        html  = request['body']
        text  = BeautifulSoup(html, "lxml").get_text().encode('utf-8').decode('us-ascii', 'ignore')

        msg      = MIMEMultipart()
        alt      = MIMEMultipart('alternative')
        htmlbody = MIMEText(html, 'html')
        textbody = MIMEText(text, 'plain')

        alt.attach(textbody)
        alt.attach(htmlbody)
        msg.attach(alt)
        for attach in request.get('attachments', []):
            msg.attach(Base64EncodedFile(attach['mime'], attach['name']))

        rcpt = request['recipient']
        if 'replyto' in request:
            name  = request['replyto'].get('name', '')
            email = request['replyto'].get('email', '')
            msg['From']     = formataddr(("{} via Scorekeeeper".format(name), self.sender))
            msg['Reply-To'] = formataddr((name, email))
        else:
            msg['From']     = formataddr(('Admin via Scorekeeeper', self.sender))
            msg['Reply-To'] = formataddr(('Scorekeeper Admin', self.replyto))

        msg['Subject']    = request['subject'].strip('\n')
        msg['Date']       = formatdate()
        msg['Message-ID'] = make_msgid(domain=self.domain)
        msg['To']         = formataddr(("{} {}".format(rcpt['firstname'], rcpt['lastname']), rcpt['email']))

        if request.get('unsub', None):
            unsub = request['unsub']
            msg['List-Id'] = "Scorekeeper {} List <{}.lists.{}>".format(unsub['listid'], unsub['listid'], self.domain)
            msg['List-Unsubscribe'] = "<{}>".format(unsub['url'])

        smtp.sendmail(self.sender, [rcpt['email']], msg.as_bytes(policy=self.policy))

