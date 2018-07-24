

"""
        "DBHOST":                          os.environ.get('DBHOST',    '/var/run/postgresql'),
        "DBPORT":                      int(os.environ.get('DBPORT',    5432)),
        "DBUSER":                          os.environ.get('DBUSER',    'localuser'),
        "MAIL_SERVER":                     os.environ.get('MAIL_SERVER',   None),
        "MAIL_DEFAULT_SENDER":             os.environ.get('MAIL_DEFAULT_SENDER', None),
 
    if theapp.config['MAIL_SERVER'] and theapp.config['MAIL_DEFAULT_SENDER']:
        theapp.mail = Mail(theapp)
"""

import logging

from sccommon.logging import logging_setup

from .sender import SenderThread

def main():
    logging_setup('/var/log/scemail.log')
    log = logging.getLogger(__name__)
    log.info("starting main")
    SenderThread().start()

