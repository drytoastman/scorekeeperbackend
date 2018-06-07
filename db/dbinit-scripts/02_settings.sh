cd /var/lib/postgresql/data

openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt -batch
chmod 400 server.key server.crt

echo "
#TYPE     DATABASE  USER                 ADDRESS         METHOD
local     all       all                                  trust    # Trust local unix sockets
hostnossl all       all                  0.0.0.0/0       reject   # force SSL for network connections
host      all       postgres,localuser   0.0.0.0/0       reject   # no postgres or localuser over the network
host      all       nulluser             0.0.0.0/0       password # allow the null user to scan for series
host      all       +driversaccess       0.0.0.0/0       password # allow any other logins with password
" > pg_hba.conf

if [ -z $UI_TIME_ZONE ]; then
UI_TIME_ZONE=US/Pacific
fi

echo "
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
log_destination = stderr
logging_collector = on
log_directory = '/var/log'
log_filename = 'scdb.log'
log_truncate_on_rotation = off
log_rotation_size = '10MB'
log_line_prefix = '%t %a '
log_timezone=$UI_TIME_ZONE
log_statement = none
log_min_duration_statement = 1000
password_encryption = off
" >> postgresql.conf

cp /docker-entrypoint-initdb.d/series.template series.sql
psql -U postgres -d scorekeeper -c "INSERT INTO version (id, version) VALUES (1, $TEMPLATE_SCHEMA_VERSION)"

