
# Scorekeeper Backend

This is a the collection of docker images that make up the Scorekeeper backend.
They include:
1. The web services
1. The database
1. The merge process

## Development

When doing development use **docker-compose** as the basis for management.  The local
docker-compose.yaml builds from local Dockerfiles and imports the code directory as active volumes.
Ex:
    docker-compose -p develop build  # compose does not automatically rebuild upon a local file change
    docker-compose -p develop up

## Docker Machine

Note that on docker-machine based systems (primarily non-Pro Windows or older Macs), mounting a local directory
into a docker container requires that the proper folder sharing is enabled in VirualBox.  The default setting
is for anything under your $HOME directory.  This is necessary for the /code volume in docker-compose.yaml
to work.

There is also a requirement to forward ports across the VirtualBox bounary.  This is done automatically
by the Java TrayMonitor application.  If that isn't running, you can do this with **docker-machine ssh** if a 
decent ssh client is available on your machine.
    docker-machine ssh default -L 80:127.0.0.1:80 -L 54329:127.0.0.1:54329 -L 127.0.0.1:5432:127.0.0.1:6432

## Deployment

For distribution, the intention is to use **docker-compose.yaml** as the base and then use create_deployment.py
to create a composition file for use in a deployed system.  It relies on docker hub for images that are
automatically built from github.

