

"""
        "DBHOST":                          os.environ.get('DBHOST',    '/var/run/postgresql'),
        "DBPORT":                      int(os.environ.get('DBPORT',    5432)),
        "DBUSER":                          os.environ.get('DBUSER',    'localuser'),
        "MAIL_USE_TLS":           any2bool(os.environ.get('MAIL_USE_TLS',  False)),
        "MAIL_USE_SSL":           any2bool(os.environ.get('MAIL_USE_SSL',  False)),
        "MAIL_SERVER":                     os.environ.get('MAIL_SERVER',   None),
        "MAIL_PORT":                       os.environ.get('MAIL_PORT',     None),
        "MAIL_USERNAME":                   os.environ.get('MAIL_USERNAME', None),
        "MAIL_PASSWORD":                   os.environ.get('MAIL_PASSWORD', None),
        "MAIL_DEFAULT_SENDER":             os.environ.get('MAIL_DEFAULT_SENDER', None),
 
    if theapp.config['MAIL_SERVER'] and theapp.config['MAIL_DEFAULT_SENDER']:
        theapp.mail = Mail(theapp)
"""

from sccommon.logging import logging_setup

def main():
    logging_setup('/var/log/scemail.log')
    print ("hello world")

