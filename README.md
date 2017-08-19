
# Scorekeeper Backend

This is a the collection of docker images that make up the Scorekeeper backend.
They include:
1. The postgresql database
1. The web services
1. The merge processor

## Development

When doing development use **docker-compose** as the basis for management.  The local
docker-compose.yaml builds from local Dockerfiles and imports the code directory as active volumes.
Eg (as compose does not automatically rebuild):
```
docker-compose -p develop build
docker-compose -p develop up
```

## Docker Machine

Note that on docker-machine based systems (primarily non-Pro Windows or older Macs), mounting a local directory
into a docker container requires that the proper folder sharing is enabled in VirualBox.  The default setting
is for anything under your $HOME directory.  This is necessary for the /code volume in docker-compose.yaml
to work.

There is also a requirement to forward ports across the VirtualBox bounary.  This is done automatically
by the Java TrayMonitor application.  If that isn't running, you can do this with **docker-machine ssh** if a 
decent ssh client is available on your machine.

```
docker-machine ssh default -L '*:80:127.0.0.1:80' -L '*:54329:127.0.0.1:54329' -L 127.0.0.1:6432:127.0.0.1:6432
```

- port 80 is shared with everyone for web access
- port 54329 is shared with everyone for remote database/merge tool access
- port 6432 is only open on 127.0.0.1 for local Java apps to connect without password


## Deployment

For distribution, the intention is to use **docker-compose.yaml** as the base and then use create_deployment.py
to create a composition file for use in a deployed system.  It relies on docker hub for images that are
automatically built from github hooks.

