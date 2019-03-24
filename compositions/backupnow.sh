docker run --rm -v $1secrets:/secrets -v $1dbsocket:/var/run/postgresql -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/scorekeeper.creds.json drytoastman/scpython backupdb scorekeeperbackup
