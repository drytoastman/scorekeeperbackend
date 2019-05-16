import json
import logging
import os
import psycopg2
import schedule
import subprocess
import time

from sccommon.logging import logging_setup

def queueEmail(body):
    args = {
                "user": "localuser",
              "dbname": "scorekeeper",
    "application_name": "cronjobs"
    }

    with psycopg2.connect(**args) as db:
        with db.cursor() as cur:
            email = dict(
                recipient = dict(
                    email = os.environ['MAIL_ADMIN_ADDRESS'],
                    firstname = 'Admin',
                    lastname = 'User'
                ),
                subject = "Scorekeeper Log Report",
                body = '<html><body><pre>'+body+'</pre></body></html>'
            )
            cur.execute("INSERT INTO emailqueue (content) VALUES (%s)", (json.dumps(email),))


def webcron():
    try:
        from nwrsc.app import cron_jobs
        cron_jobs()
    except Exception as e:
        logging.getLogger("webcron").error("Failed ro run webcron: %s", e)


def backup():
    try:
        from sccommon.backuprestore import backup_db
        backup_db('scorekeeperbackup')
    except Exception as e:
        logging.getLogger("backup").error("Failed ro run backup: %s", e)


def mailerrors():
    try:
        from sccommon.logging import collect_errors
        errors = collect_errors()
        txt = list()
        for k in sorted(errors.keys()):
            txt.append('\nFILE: {}\n'.format(k))
            txt.extend(errors[k])
    except Exception as e:
        txt = ["Failed to collect errors: {}".format(e)]

    queueEmail('\n'.join(txt))


def crondaemon():
    logging_setup('/var/log/sccron.log')

    # UTC
    schedule.every().day.at("08:00").do(backup)  # 1:00 AM PDT
    schedule.every().day.at("11:00").do(webcron) # 4:00 AM PDT
    schedule.every().day.at("20:00").do(backup)  # 1:00 PM PDT
    schedule.every().day.at("03:00").do(mailerrors) # 8:00 PM PDT

    while True:
        schedule.run_pending()
        time.sleep(60)
