
# Scorekeeper Backend

This is a the collection of docker images that make up the Scorekeeper backend.
They include:
    1. The web services
    1. The database
    1. The merge process

## Development

When doing development use **docker-compose -f docker-compose-dev.yaml** as the basis for composition.
This builds from local Dockerfiles and imports the code directories as active volumes.

Note that on docker-machine based systems (primarily non-Pro Windows), this directory must be under your
$HOME directory or else it won't make it across the VirtualBox boundary share and the /code volume in 
docker-compose-dev.yaml won't show up.

## Deployment

For distribution, the intention is to use **docker-compose.yaml** as the composition.  This will draw
on docker hub for images that are automatically built from github.

