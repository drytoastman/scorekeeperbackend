#!/usr/bin/env python3

import datetime
import itertools
import json
import psycopg2
import psycopg2.extras
import re
import sys
import time

psycopg2.extras.register_uuid()
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

def print_log(table, action, otime, ltime, old, new, idfield):
    if action == 'I':
        print("{} Insert {}: {}, {}, {}".format(table, new[idfield], otime, ltime, ""))
        return
    elif action == 'D':
        print("{} Delete {}: {}, {}, {}".format(table, old[idfield], otime, ltime, ""))
        return

    # else update
    for k in list(old.get('attr',dict()).keys()):
        old[k] = old['attr'].pop(k)
    for k in list(new.get('attr',dict()).keys()):
        new[k] = new['attr'].pop(k)

    diff = {}
    for k in new:
        if k not in old:
           diff[k] = (None, new[k])
        elif old[k] != new[k]:
           diff[k] = (old[k], new[k])
    print("{} Update {}: {}, {}, {}".format(table, old[idfield], otime, ltime, diff))


def parse_dump_file(name):
    startdata = re.compile(r'^COPY (\w+) ')

    with open(name, 'r') as fp:
        for line in fp:
            s = startdata.search(line)
            if s and s.group(1) == 'publiclog':
                for line in fp:
                    if line.strip() == '\\.':
                        break
                    (logid, series, app, table, action, otime, ltime, old, new) = line.strip().split('\t')
                    print_log(table, action, otime, ltime, json.loads(old), json.loads(new))

def parse_drivers(port):
    db = connect_port(port)
    with db.cursor() as cur:
        cur.execute("select * from publiclog where tablen='drivers' order by otime")
        for row in cur.fetchall():
            print_log(row['tablen'], row['action'], row['otime'], row['ltime'], row['olddata'], row['newdata'], 'driverid')
        cur.execute("select * from drivers")
        for row in cur.fetchall():
            print(row)

def parse_runs(port, series):
    db = connect_port(port)
    with db.cursor() as cur:
        cur.execute("set search_path=%s,'public'", (series,))
        cur.execute("select * from serieslog where tablen='runs' order by otime")
        for row in cur.fetchall():
            print_log(row['tablen'], row['action'], row['otime'], row['ltime'], row['olddata'], row['newdata'], 'carid')


def list_diff(old, new):
    for ii, (oldid, newid) in enumerate(itertools.zip_longest(old, new)):
        if oldid != newid:
            print("{}: {} -> {}".format(ii, oldid, newid))


def get_names(db):
    ret = dict()
    with db.cursor() as cur:
        cur.execute("select c.carid, c.classcode, d.firstname, d.lastname from drivers d JOIN cars c ON c.driverid=d.driverid")
        for row in cur.fetchall():
            ret[str(row['carid'])] = "{} {} ({})".format(row['firstname'], row['lastname'], row['classcode'])
    return ret

def parse_runorder_changes(port, series):
    db = connect_port(port)
    with db.cursor() as cur:
        cur.execute("set search_path=%s,'public'", (series,))
        cur.execute("select * from serieslog where tablen='runorder' and action='U' order by otime")
        names = get_names(db)
        for row in cur.fetchall():
            otime = row['otime']
            print("{} - Course {}  - RunGroup {}".format(otime - datetime.timedelta(hours=8), row['newdata']['course'], row['newdata']['rungroup']))
            old = [names[cid] for cid in row['olddata']['cars']]
            new = [names[cid] for cid in row['newdata']['cars']]
            list_diff(old, new)

def connect_port(port):
    args = {
      "cursor_factory": psycopg2.extras.DictCursor,
                "host": "127.0.0.1",
                "port": port,
                "user": "postgres",
              "dbname": "scorekeeper",
    "application_name": "inspector"
    }
    return psycopg2.connect(**args)


if __name__ == '__main__':
    parse_runorder_changes(6432, 'pro2019')

    #parse_runs(int(sys.argv[1]), sys.argv[2])
    #parse_dump_file(sys.argv[1])

