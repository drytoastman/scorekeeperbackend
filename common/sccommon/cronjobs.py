import schedule
import subprocess
import time

def crondaemon():
    def webcron():
        from nwrsc.app import cron_jobs
        cron_jobs()

    def backup():
        from sccommon.backuprestore import backup_db
        backup_db('scorekeeperbackup')

    # UTC
    schedule.every().day.at("11:00").do(webcron)
    schedule.every().day.at("11:30").do(backup)

    while True:
        schedule.run_pending()
        time.sleep(60)
