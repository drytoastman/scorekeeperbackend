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

echo "
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
" >> postgresql.conf

cp /docker-entrypoint-initdb.d/series.template series.sql
 
