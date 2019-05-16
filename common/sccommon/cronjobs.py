import logging
import schedule
import subprocess
import time

from sccommon.logging import logging_setup

def crondaemon():
    logging_setup('/var/log/sccron.log')

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
        except Exception as e:
            errors = ["Failed to collect errors: {}".format(e)]

        print(errors)
        # mail here

 
    # UTC
    schedule.every().day.at("08:00").do(backup)  # 1:00 AM PDT
    schedule.every().day.at("11:00").do(webcron) # 4:00 AM PDT
    schedule.every().day.at("20:00").do(backup)  # 1:00 PM PDT
    schedule.every().day.at("03:00").do(mailerrors) # 8:00 PM PDT

    while True:
        schedule.run_pending()
        time.sleep(60)
