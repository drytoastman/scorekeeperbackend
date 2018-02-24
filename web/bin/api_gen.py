#!/usr/bin/env python3
import os, subprocess, sys

def root():
    pypath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    try:
        path = subprocess.run(["cygpath", "-w", pypath], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
        if path is not None:
            return path
    except:
        pass
    return pypath

subprocess.run(['docker', 'run', '--rm', '-v', root()+':/local', 'swaggerapi/swagger-codegen-cli:v2.3.1', 'generate', '-i/local/nwrsc/api/swagger.yaml', '-o/local', '-lpython-flask', '-Dmodels', '-DpackageName=nwrsc.api'])

