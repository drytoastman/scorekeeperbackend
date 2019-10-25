#!/usr/bin/env python3

import argparse
import psycopg2
import psycopg2.extras
import sqlite3

class AttrWrapper(object):
    def __init__(self, tup, headers):
        for k,v in zip(headers, tup):
            setattr(self, k, v)

def createseries(srcdb, name, password):
    old = sqlite3.connect(srcdb)
    old.row_factory = sqlite3.Row

    new = psycopg2.connect(host='127.0.0.1', port=6432, user='postgres', dbname='scorekeeper', application_name='legacycreate', cursor_factory=psycopg2.extras.DictCursor)
    cur = new.cursor()

    cur.execute("select schema_name from information_schema.schemata where schema_name=%s", (name,))
    if cur.rowcount > 0:
        raise Exception("{} is already an active series, not continuing".format(name))

    cur.execute("select verify_user(%s, %s)", (name, password))
    cur.execute("select verify_series(%s)", (name,))
    cur.execute("set search_path=%s,%s", (name, 'public'))

    #INDEXLIST 
    print("\tindexes")
    cur.execute("insert into indexlist values ('', 'No Index', 1.000, now())")
    allindexcodes = set()
    for r in old.execute("select * from indexlist"):
        i = AttrWrapper(r, r.keys())
        cur.execute("insert into indexlist values (%s, %s, %s, now())",     
                    (i.code, i.descrip, i.value))
        allindexcodes.add(i.code)


    #CLASSLIST
    print("\tclasses")
    cur.execute("insert into classlist values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())", 
                ('_HOLD', 'Placeholder Class', '', '', 1.0, False, False, False, False, False, 0))
    allclasscodes = set()
    for r in old.execute("select * from classlist"):
        c = AttrWrapper(r, r.keys())
        c.usecarflag  = c.usecarflag and True or False
        c.carindexed  = c.carindexed and True or False
        c.eventtrophy = c.eventtrophy and True or False
        c.champtrophy = c.champtrophy and True or False
        c.secondruns  = c.code in ('TOPM', 'ITO2')
        cur.execute("insert into classlist values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())", 
                    (c.code, c.descrip, c.classindex, c.caridxrestrict, c.classmultiplier, c.carindexed, c.usecarflag, c.eventtrophy, c.champtrophy, c.secondruns, c.countedruns))
        allclasscodes.add(c.code)


    #SETTINGS
    print("\tsettings")
    settings = dict()
    for r in old.execute("select name,val from settings"):
        key = r['name']
        val = r['val']
        if key == 'useevents':
            key = 'dropevents'
        cur.execute("insert into settings values (%s, %s, now())", (key, val))


    old.close()
    new.commit()
    new.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a new series from an old legacy database')
    parser.add_argument('--srcdb',    required=True, help='the database files to work from')
    parser.add_argument('--name',     required=True, help='the new series name')
    parser.add_argument('--password', required=True, help='the new series password')
    args = parser.parse_args()
    createseries(args.srcdb, args.name, args.password)

