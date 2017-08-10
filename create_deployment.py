#!/usr/bin/env python

# Read in docker-compose.yaml file and create a deployment version on stdout

import sys
import yaml

if len(sys.argv) < 2:
    print ("Usage:\n\n{} version\n".format(sys.argv[0]))
    sys.exit(0)

fp = open('docker-compose.yaml', 'r')
compose = yaml.load(fp.read())
fp.close()

for name in ('web', 'db'):
    service = compose['services'][name]
    # Add image
    service['image'] = "drytoastman/sc{}:{}".format(name, sys.argv[1])
    # Remove build and command overrides
    service.pop('build',   None)
    service.pop('command', None)
    # Filter out any local directory mountings or debug environment variables
    service['volumes']     = filter(lambda v: not (v.startswith('/') or v.startswith('.')), service.get('volumes', []))
    service['environment'] = filter(lambda e: 'DEBUG' not in e, service.get('environment', []))

print yaml.safe_dump(compose)
