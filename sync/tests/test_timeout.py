#!/usr/bin/env python3

import datetime
import json
import logging
import pytest
import subprocess
import time

from helpers import *

log = logging.getLogger(__name__)

@pytest.mark.timeout(60, method='thread')
def test_driversync(syncdbs, syncdata):
    """ Testing network disconnects """
    syncx, mergex = syncdbs

    def progress(action, table):
        if action == 'update' and table == 'cars':
            subprocess.run(["docker", "network", "disconnect", "bridge", "syncB"])
            
    mergex['A'].listener = progress

    # Modify firstname and address on A
    with syncx['A'].cursor() as cur:
        cur.execute("UPDATE drivers SET firstname=%s,attr=%s,modified=now() where driverid=%s", ('newfirst', json.dumps({'address': '123'}), syncdata.driverid,))
        cur.execute("UPDATE cars SET number=666,modified=now() where carid=%s", (syncdata.carid,))
        syncx['A'].commit()
    time.sleep(0.1)

    dosync(syncx['A'], mergex['A'])

