#!/usr/bin/env bash
set -e

# Make sure postgres can wrie to /var/log
chown postgres:postgres /var/log

# Update our series template file any time we can, not just on database init of volume
if [ -s "$PGDATA/PG_VERSION" ]; then
    cp "/docker-entrypoint-initdb.d/series.template" "$PGDATA/series.sql"

    # REMOVE LATER: temp command to rewrite duration log on already created databases
    sed -i '/log_min_duration_statement/c\log_min_duration_statement = 1000' /var/lib/postgresql/data/postgresql.conf
fi 


# Run the regular entrypoint but use -C to get it to drop out after init is done
/usr/local/bin/docker-entrypoint.sh -C data_directory

# Start our socat bridge, only after init is done, otherwise clients can connect to the db
# during initialization and then lose the connection when it restarts
socat TCP-LISTEN:6432,reuseaddr,fork, UNIX-CLIENT:/var/run/postgresql/.s.PGSQL.5432 &

# Start postgres here
exec /usr/local/bin/docker-entrypoint.sh "$@"
