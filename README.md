
# Scorekeeper Backend

This is a the collection of docker images that make up the Scorekeeper backend.
They include:
1. The web services
1. The database
1. The merge process

## Development

When doing development use **docker-compose -f docker-compose-dev.yaml** as the basis for composition.
This builds from local Dockerfiles and imports the code directories as active volumes.

## Docker Machine

Note that on docker-machine based systems (primarily non-Pro Windows or older Macs), mounting a local directory
into a docker container requires that the proper folder sharing is enabled in VirualBox.  The default setting
is for anything under your $HOME directory.  This is necessary for the /code volume in docker-compose-dev.yaml
to work.

There is also a requirement to forward ports across the VirtualBox bounary.  This is done automatically
by the Java TrayMonitor application.  If that isn't running, you can do this with **docker-machine ssh** if a 
decent ssh client is available on your machine.
    docker-machine ssh default -L 80:127.0.0.1:80 -L 54329:127.0.0.1:54329

## Deployment

For distribution, the intention is to use **docker-compose.yaml** as the composition.  This will draw
on docker hub for images that are automatically built from github.

