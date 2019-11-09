cd /var/lib/postgresql/data

if [ $NOCLIENTCERT ]; then
    APPEND=""
else
    APPEND="clientcert=1"
fi

echo "
#TYPE     DATABASE  USER                 ADDRESS         METHOD
local     all       all                                  trust    # Trust local unix sockets
hostnossl all       all                  0.0.0.0/0       reject   # force SSL for network connections
hostssl   all       postgres,localuser   0.0.0.0/0       reject   $APPEND # no postgres or localuser over the network
hostssl   all       nulluser             0.0.0.0/0       password $APPEND # allow the null user to scan for series
hostssl   all       +driversaccess       0.0.0.0/0       password $APPEND # allow any other logins with password
" > pg_hba.conf

if [ -z $UI_TIME_ZONE ]; then
UI_TIME_ZONE=US/Pacific
fi

echo "
ssl = on
ssl_ca_file = '/certs/root.cert'
ssl_cert_file = '/certs/server.cert'
ssl_key_file = '/certs/server.key'
logging_collector = on
log_destination = stderr
log_directory = '/var/log'
log_filename = 'scdb.log'
log_truncate_on_rotation = off
log_rotation_size = '10MB'
log_line_prefix = '%t %a '
log_timezone=$UI_TIME_ZONE
log_statement = none
log_min_duration_statement = 1000
" >> postgresql.conf

cp /docker-entrypoint-initdb.d/series.template series.sql
psql -U postgres -d scorekeeper -c "INSERT INTO version (id, version) VALUES (1, $TEMPLATE_SCHEMA_VERSION)"
