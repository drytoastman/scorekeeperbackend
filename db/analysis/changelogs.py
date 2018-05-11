#!/usr/bin/env python3

import json
import re
import sys


def parse_publiclog(fp):
    for line in fp:
        if line.strip() == '\\.':
            return
        (logid, series, app, table, action, otime, ltime, old, new) = line.strip().split('\t')
        old = json.loads(old)
        new = json.loads(new)

        if table != 'drivers':
            continue

        if action == 'I':
            print("Insert {}: {}".format(new['driverid'], new))
            continue
        elif action == 'D':
            print("Delete {}: {}".format(old['driverid'], old))
            continue

        # else update
        for k in list(old['attr'].keys()):
            old[k] = old['attr'].pop(k)
        for k in list(new['attr'].keys()):
            new[k] = new['attr'].pop(k)
            
        diff = {}
        for k in new:
            if k not in old:
               diff[k] = (None, new[k]) 
            elif old[k] != new[k]:
               diff[k] = (old[k], new[k]) 
        print("Update {}: {}, {}, {}".format(old['driverid'], otime, ltime, diff))


def parse_dump_file(name):
    startdata = re.compile(r'^COPY (\w+) ')
   
    with open(name, 'r') as fp:
        for line in fp:
            s = startdata.search(line)
            if s and s.group(1) == 'publiclog':
                parse_publiclog(fp)
                print("done table")

if __name__ == '__main__':
    parse_dump_file(sys.argv[1])

