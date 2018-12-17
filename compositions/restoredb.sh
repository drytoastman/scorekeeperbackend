docker run -v $1secrets:/secrets -v $1scsocket:/var/run/postgresql -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/scorekeeper.creds.json drytoastman/scpython restoredb scorekeeperbackup
