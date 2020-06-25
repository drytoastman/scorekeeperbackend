#!/usr/bin/env python  
import logging 
import sys  
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout) 
import nwrsc.app
nwrsc.app.cron_jobs()
