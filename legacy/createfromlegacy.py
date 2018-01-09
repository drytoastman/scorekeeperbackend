#!/usr/bin/env python3

import argparse
import glob
import json
import os
import psycopg2
import psycopg2.extras
import random
import sqlite3
import sys
import uuid

from flask import g
from nwrsc.model import Result, Series
from nwrsc.app import create_app

class AttrWrapper(object):
    def __init__(self, tup, headers):
        for k,v in zip(headers, tup):
            setattr(self, k, v)

def idgen():
    """ randomize timelow so that are quick entry ids require less characters to find a match """
    v1 = uuid.uuid1()
    return uuid.UUID(fields=(int(random.uniform(0, 0xFFFFFFFF)), v1.time_mid, v1.time_hi_version, v1.clock_seq_hi_variant, v1.clock_seq_low, v1.node), version=1)


def createseries(srcdb, name, password, copycars):

    old = sqlite3.connect(srcdb)
    old.row_factory = sqlite3.Row

    psycopg2.extras.register_uuid()
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
                ('HOLD', 'Unknown Class', '', '', 1.0, False, False, False, False, False, 0))
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


    ## if copying cars, pull over drivers as well
    if copycars:
        remapdriver = dict()

        #DRIVERS, add to global list and remap ids as necessary
        print("\tdrivers")
        for r in old.execute("select d.* from drivers d WHERE d.id in (select driverid from cars c WHERE c.id in (SELECT carid from runs) AND c.classcode NOT LIKE '%NOV%' AND c.classcode NOT LIKE 'TO%') AND d.email like '%@%'"):
            d = AttrWrapper(r, r.keys())

            cur.execute("select * from drivers where lower(firstname)=%s and lower(lastname)=%s and lower(email)=%s", 
                        (d.firstname.strip().lower(), d.lastname.strip().lower(), d.email.strip().lower()))
            if cur.rowcount > 0:
                match = cur.fetchone()
                remapdriver[d.id] = match['driverid']
                print('\t\tmatch %s %s %s' % (d.firstname, d.lastname, d.email))
            else:
                newd = dict()
                newd['driverid']   = idgen()
                newd['firstname']  = d.firstname.strip()
                newd['lastname']   = d.lastname.strip()
                newd['email']      = d.email.strip()
                newd['username']   = str(newd['driverid']) # Fake for now
                newd['password']   = ""
                newd['membership'] = d.membership and d.membership.strip() or ""
                newd['optoutmail'] = False
                newd['attr']       = dict()
                for a in ('alias', 'address', 'city', 'state', 'zip', 'phone', 'brag', 'sponsor', 'notes'):
                    if hasattr(d, a) and getattr(d, a):
                        newd['attr'][a] = getattr(d, a).strip()
        
                cur.execute("insert into drivers values (%s, %s, %s, %s, %s, %s, %s, %s, %s, now())", 
                    (newd['driverid'], newd['firstname'], newd['lastname'], newd['email'], newd['username'], newd['password'], newd['membership'], newd['optoutmail'], json.dumps(newd['attr'])))
                remapdriver[d.id] = newd['driverid']

        #CARS (all the same fields, need to map carid and driverid)
        print("\tcars")
        for r in old.execute("select * from cars"):
            c = AttrWrapper(r, r.keys())
            if c.driverid < 0:
                continue
            if c.driverid not in remapdriver:
                print("\t\tskipping car with unknown driverid {}".format(c.driverid))
                continue
            if c.classcode not in allclasscodes:
                print("\t\tassigning unknown class {} to HOLD".format(c.classcode))
                c.classcode = 'HOLD'
            if c.indexcode and c.indexcode not in allindexcodes:
                print("\t\tassigning unknown index {} to AM".format(c.indexcode))
                c.indexcode = 'AM'
            newc = dict()
            newc['carid']      = idgen()
            newc['driverid']   = remapdriver[c.driverid]
            newc['classcode']  = c.classcode
            newc['indexcode']  = c.indexcode or ''
            newc['number']     = c.number or 999
            newc['useclsmult'] = bool(getattr(c, 'tireindexed', False))
            newc['attr']       = dict()
            for a in ('year', 'make', 'model', 'color'):
                if hasattr(c, a) and getattr(c, a):
                    newc['attr'][a] = getattr(c, a)

            cur.execute("insert into cars values (%s, %s, %s, %s, %s, %s, %s, now())", 
                (newc['carid'], newc['driverid'], newc['classcode'], newc['indexcode'], newc['number'], newc['useclsmult'], json.dumps(newc['attr'])))

        
    old.close()
    new.commit()
    new.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a new series from an old legacy database')
    parser.add_argument('--srcdb', required=True, help='the database files to work from')
    parser.add_argument('--name',  required=True, help='the new series name')
    parser.add_argument('--password', required=True, help='the new series password')
    parser.add_argument('--cars', action='store_true', help='whether to include cars and matching drivers as well')
    args = parser.parse_args()
    app = create_app()
    random.seed()
    createseries(args.srcdb, args.name, args.password, args.cars)

