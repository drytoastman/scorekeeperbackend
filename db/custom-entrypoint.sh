#!/usr/bin/env bash
set -e

# Start our socat bridge and then call out to the original startup
socat TCP-LISTEN:6432,reuseaddr,fork, UNIX-CLIENT:/var/run/postgresql/.s.PGSQL.5432 &

# Make sure postgres can wrie to /var/log
chown postgres:postgres /var/log

# Update our series template file any time we can, not just on database init of volume
if [ -s "$PGDATA/PG_VERSION" ]; then
    cp "/docker-entrypoint-initdb.d/series.template" "$PGDATA/series.sql"
fi 

# Run the regular entrypoint
exec /usr/local/bin/docker-entrypoint.sh "$@"
