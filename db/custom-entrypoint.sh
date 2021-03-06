#!/usr/bin/env bash
set -e

# Make sure postgres can wrie to /var/log
chown postgres:postgres /var/log

# Make sure our keys are present and correctly labeled, normally a volume is mapped at /certs
if [ ! -d /certs ]; then
    mkdir -p /certs
fi

if [ ! -f "/certs/root.cert" ]; then
    /docker-entrypoint-initdb.d/certgen.bash /certs missing
fi

chmod -f 600 /certs/*
chown -f postgres:postgres /certs/*

# Update our series template file any time we can, not just on database init of volume
if [ -s "$PGDATA/PG_VERSION" ]; then
    cp "/docker-entrypoint-initdb.d/series.template" "$PGDATA/series.sql"
fi

# Run the regular entrypoint but use -C to get it to drop out after init is done
/usr/local/bin/docker-entrypoint.sh -C data_directory

# Start our socat bridge, only after init is done, otherwise clients can connect to the db
# during initialization and then lose the connection when it restarts
socat TCP-LISTEN:6432,reuseaddr,fork, UNIX-CLIENT:/var/run/postgresql/.s.PGSQL.5432 &

# Start postgres here
exec /usr/local/bin/docker-entrypoint.sh "$@"
