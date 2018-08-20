# Scorekeeper Backend

[![Build Status](https://travis-ci.org/drytoastman/scorekeeperbackend.svg?branch=master)](https://travis-ci.org/drytoastman/scorekeeperbackend)
[![Security Status](https://snyk.io/test/github/drytoastman/scorekeeperbackend/badge.svg?targetFile=scpythonbase/requirements.txt)](https://snyk.io/test/github/drytoastman/scorekeeperbackend)

This is a the collection of docker images that make up the Scorekeeper backend.
They include:
1. The postgresql database
1. The web services 
1. The sync processor
1. The mailman processor

## Development

When doing development use **docker-compose** as the basis for management expect for the base image.  The local
docker-compose.yaml builds from local Dockerfiles and imports the code directories as active volumes.
Eg (as compose does not automatically rebuild):
```
docker build -t scpythonbase scpythonbase
docker-compose build
docker-compose up
```

## Docker Machine

Note that on docker-machine based systems (primarily non-Pro Windows or older Macs), mounting a local directory
into a docker container requires that the proper folder sharing is enabled in VirualBox.  The default setting
is for anything under your $HOME directory.  This is necessary for the /code volume in docker-compose.yaml
to work.

There is also a requirement to forward ports across the VirtualBox bounary.  This is done automatically
by the Java TrayApplication.  If that isn't running, you can do this with **docker-machine ssh** if a 
decent ssh client is available on your machine.

```
docker-machine ssh default -L '*:80:127.0.0.1:80' -L '*:54329:127.0.0.1:54329' -L 127.0.0.1:6432:127.0.0.1:6432
```

- port 80 is shared with everyone for web access
- port 54329 is shared with everyone for remote database/merge tool access
- port 6432 is only open on 127.0.0.1 for local Java apps to connect without password


## Deployment

For systems not using the frontend monitor application to control the backend, you can use **docker-compose.yaml**
as the basis for your docker-composition file.  scorekeeper.wwscc.org uses a modified version of this file that 
removes the sync server and uses a different set of environment variables.

## Apache Forwarding

For our OS X Server based on Apache, we can't quite set it up the way we want so we do the basics with the GUI
configuration and then add the following lines to site configuration file to proxy most URLs to our local container.
The .well-known line is one way of letting some URLs use the regular filesystem for serving files.

```
ProxyPass /.well-known !
ProxyPass / http://127.0.0.1:9999/
ProxyPassReverse / http://127.0.0.1:9999/
```

