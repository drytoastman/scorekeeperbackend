#!/usr/bin/env python3

import schedule
import subprocess
import time

def cloudbackup():
    subprocess.run(['cloudbackup.py', '--creds', '/secrets/scorekeeperbackup.creds.json', '--backup'])

def squarerenew():
    subprocess.run(['wget', 'http://web/cron'])

schedule.every().hour.do(squarerenew)
schedule.every().day.at("3:30").do(cloudbackup)

while True:
    schedule.run_pending()
    time.sleep(60)
