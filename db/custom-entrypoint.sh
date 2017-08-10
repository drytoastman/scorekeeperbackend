#!/usr/bin/env bash
set -e
# Start our socat bridge and then call out to the original startup
socat TCP-LISTEN:6432,reuseaddr,fork, UNIX-CLIENT:/var/run/postgresql/.s.PGSQL.5432 &
exec /usr/local/bin/docker-entrypoint.sh postgres
