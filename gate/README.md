
This is a single image pgbouncer component of ScorekeeperBackend that provides a path to the trusted
unix socket for localhost connections so they can use the postgres and localuser roles.  This is necessary
for docker-machine (some OS X, most Windows) users who can't share a unix socket with the container.

For development, see the README in the root directory of https://github.com/drytoastman/scorekeeperbackend

