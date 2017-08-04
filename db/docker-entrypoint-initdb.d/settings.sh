cd /var/lib/postgresql/data

openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt -batch
chmod 400 server.key server.crt

echo "
#TYPE     DATABASE  USER                 ADDRESS         METHOD
local     all       all                                  trust    # Trust local unix sockets
host      all       postgres,localuser   127.0.0.1/32    trust    # No password for local access
host      all       postgres,localuser   192.168.24.0/24 trust    # No password for access from the local docker network
host      all       postgres,localuser   0.0.0.0/0       reject   # no postgres or localuser off site
hostnossl all       all                  0.0.0.0/0       reject   # force SSL for non-localhost connections
host      all       +driversaccess       0.0.0.0/0       password # allow any other logins with password
" > pg_hba.conf

echo "
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
" >> postgresql.conf

