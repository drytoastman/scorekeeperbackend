#!/usr/bin/env python3

import schedule
import subprocess
import time


def cloudbackup():
    subprocess.run(['cloudbackup.py', '--creds', '/secrets/scorekeeper.creds.json', '--backup'])

def webcron():
    from nwrsc.app import cron_jobs
    cron_jobs()

# UTC
schedule.every().day.at("11:00").do(webcron)
schedule.every().day.at("11:30").do(cloudbackup)

while True:
    schedule.run_pending()
    time.sleep(60)
