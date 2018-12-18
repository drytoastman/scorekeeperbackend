import logging
import schedule
import subprocess
import time

def crondaemon():
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
 
    # UTC
    schedule.every().day.at("11:00").do(webcron)
    schedule.every().day.at("11:30").do(backup)

    while True:
        schedule.run_pending()
        time.sleep(60)
