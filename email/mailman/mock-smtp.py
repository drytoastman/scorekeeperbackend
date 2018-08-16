#!/usr/bin/env python3

import asyncore
import email
import email.utils
import logging
import os
import smtpd
import sys

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class MockSMTPServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        logging.info('%s => %s', mailfrom, rcpttos)
        msg  = email.message_from_bytes(data)
        logging.info(msg)
        
logging.info('Starting up Mock SMTP server')
smtp_server = MockSMTPServer((os.getenv('MOCK_SMTP_ADDRESS', '127.0.0.1'), int(os.getenv('MOCK_SMTP_PORT', '25'))), None)

try:
    asyncore.loop()
except (KeyboardInterrupt, asyncore.ExitNow):
    pass
except Exception as ex:
    logging.exception(ex)

smtp_server.close()

