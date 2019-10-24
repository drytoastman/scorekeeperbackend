#!/bin/bash
if [ $# -ne 2 ]; then
    echo -e "\n\tUsage: $0 [secretsvol] [dbsocketvol]\n";
    exit -1;
fi
docker run --rm -v $1:/secrets -v $2:/var/run/postgresql -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/scorekeeper.creds.json drytoastman/scpython restoredb scorekeeperbackup
