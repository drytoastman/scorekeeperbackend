#!/usr/bin/env python3

import glob
import json
import os
import psycopg2
import psycopg2.extras
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

def convert(sourcefile, archive):
    remapdriver    = dict()
    remapcar       = dict({-1:None})
    remapevent     = dict()
    remapchallenge = dict()
    challengeruns  = list()
    name = os.path.basename(sourcefile[:-3]).lower()

    old = sqlite3.connect(sourcefile)
    old.row_factory = sqlite3.Row

    for r in old.execute("select value from passwords where tag='series'"):
        password = r['value']
    print("{} - password {}".format(name, password))

    # Assumes that we are running in a docker container along side db
    psycopg2.extras.register_uuid()
    new = psycopg2.connect(host='/var/run/postgresql', user='postgres', dbname='scorekeeper', application_name='oldimport', cursor_factory=psycopg2.extras.DictCursor)
    cur = new.cursor()

    cur.execute("select schema_name from information_schema.schemata where schema_name=%s", (name,))
    if cur.rowcount > 0:
        raise Exception("{} is already an active series, not continuing".format(name))

    cur.execute("select verify_user(%s, %s)", (name, password))
    cur.execute("select verify_series(%s)", (name,))
    cur.execute("set search_path=%s,%s", (name, 'public'))

    #DRIVERS, add to global list and remap ids as necessary
    print("\tdrivers")
    for r in old.execute('select * from drivers'):
        d = AttrWrapper(r, r.keys())

        cur.execute("select * from drivers where lower(firstname)=%s and lower(lastname)=%s and lower(email)=%s", 
                    (d.firstname.strip().lower(), d.lastname.strip().lower(), d.email.strip().lower()))
        if cur.rowcount > 0: # and d.email.strip().lower():
            match = cur.fetchone()
            remapdriver[d.id] = match['driverid']
            print('\t\tmatch %s %s %s' % (d.firstname, d.lastname, d.email))
        else:
            newd = dict()
            newd['driverid']   = uuid.uuid1()
            newd['firstname']  = d.firstname.strip()
            newd['lastname']   = d.lastname.strip()
            newd['email']      = d.email.strip()
            newd['username']   = str(uuid.uuid1()) # Fake for now
            newd['password']   = ""
            newd['membership'] = d.membership and d.membership.strip() or ""
            newd['attr']       = dict()
            for a in ('alias', 'address', 'city', 'state', 'zip', 'phone', 'brag', 'sponsor', 'notes'):
                if hasattr(d, a) and getattr(d, a):
                    newd['attr'][a] = getattr(d, a).strip()
    
            cur.execute("insert into drivers values (%s, %s, %s, %s, %s, %s, %s, %s, now())", 
                (newd['driverid'], newd['firstname'], newd['lastname'], newd['email'], newd['username'], newd['password'], newd['membership'], json.dumps(newd['attr'])))
            remapdriver[d.id] = newd['driverid']


    #INDEXLIST 
    print("\tindexes")
    cur.execute("insert into indexlist values ('', 'No Index', 1.000, now())")
    allindexcodes = set()
    for r in old.execute("select * from indexlist"):
        i = AttrWrapper(r, r.keys())
        cur.execute("insert into indexlist values (%s, %s, %s, now())",     
                    (i.code, i.descrip, i.value))
        allindexcodes.add(i.code)


    #CLASSLIST (map seriesid)
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


    #CARS (all the same fields, need to map carid, driverid and seriesid)
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
        newc['carid']      = uuid.uuid1()
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
        remapcar[c.id] = newc['carid']

        
    #EVENTS (all the same fields)
    print("\tevents")
    for r in old.execute("select * from events"):
        e = AttrWrapper(r, r.keys())
        segments = e.segments
        if segments:
            segments = len(e.segments.replace(" ", "").split(","))
        else:
            segments = 0
        newe = dict()
        newe['eventid']     = uuid.uuid1()
        newe['name']        = e.name or "No Name"
        newe['date']        = e.date
        newe['regopened']   = e.regopened
        newe['regclosed']   = e.regclosed
        newe['courses']     = e.courses
        newe['runs']        = e.runs
        newe['countedruns'] = e.countedruns or 0
        newe['segments']    = segments
        newe['perlimit']    = e.perlimit or 0
        newe['sinlimit']    = e.totlimit or 0
        newe['totlimit']    = e.totlimit or 0
        newe['conepen']     = e.conepen
        newe['gatepen']     = e.gatepen
        newe['ispro']       = e.ispro and True or False
        newe['ispractice']  = e.practice and True or False
        newe['attr']        = dict()

        for a in ('location', 'sponsor', 'host', 'chair', 'designer', 'snail', 'cost', 'notes', 'doublespecial'):
            if hasattr(e, a) and getattr(e, a):
                newe['attr'][a] = getattr(e, a)

        cur.execute("insert into events values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())", 
            (newe['eventid'], newe['name'], newe['date'], newe['regopened'], newe['regclosed'], newe['courses'], newe['runs'], newe['countedruns'], newe['segments'],
            newe['perlimit'], newe['sinlimit'], newe['totlimit'], newe['conepen'], newe['gatepen'], newe['ispro'], newe['ispractice'], json.dumps(newe['attr'])))

        remapevent[e.id] = newe['eventid']

    #REGISTERED (map carid)
    print("\tregistered")
    for r in old.execute("select * from registered"):
        oldr = AttrWrapper(r, r.keys())
        if oldr.eventid > 0x0FFFF:
            continue
        if oldr.carid in remapcar:
            cur.execute("insert into registered values (%s, %s, NULL, now())", (remapevent[oldr.eventid], remapcar[oldr.carid]))
        else:
            print("\t\tskipping unknown carid {}".format(oldr.carid))


    #CLASSORDER
    print("\tclassorder")
    for r in old.execute("select * from rungroups"):
        oldr = AttrWrapper(r, r.keys())
        if not oldr.classcode:
            print("\t\tskipping blank classcode in classorder table")
            continue
        if oldr.classcode not in allclasscodes:
            print("\t\tassigning unknown class {} to HOLD".format(oldr.classcode))
            oldr.classcode = 'HOLD'
        cur.execute("insert into classorder values (%s, %s, %s, %s, now())", (remapevent[oldr.eventid], oldr.classcode, oldr.rungroup, oldr.gorder))


    #RUNORDER 
    print("\trunorder")
    uniqueorder = set()
    for r in old.execute("select * from runorder order by row"):
        oldr = AttrWrapper(r, r.keys())
        key = (oldr.eventid, oldr.course, oldr.rungroup, oldr.row)
        if key in uniqueorder:
            print("\t\tskipping duplicate runorder row {}".format(key))
            continue
        uniqueorder.add(key)
		
        if oldr.carid in remapcar:
            cur.execute("insert into runorder values (%s, %s, %s, %s, %s, now())", (remapevent[oldr.eventid], oldr.course, oldr.rungroup, oldr.row, remapcar[oldr.carid]))
        else:
            print("\t\tskipping unknown carid {}".format(oldr.carid))


    #RUNS (map eventid, carid)
    print("\truns")
    for r in old.execute("select * from runs"):
        oldr = AttrWrapper(r, r.keys())
        if (oldr.eventid > 0x0FFFF):
            if not oldr.reaction: oldr.reaction = 0
            if not oldr.sixty: oldr.sixty = 0
            challengeruns.append(oldr)
            continue
            
        attr = dict()
        if oldr.reaction: attr['reaction'] = oldr.reaction
        if oldr.sixty:    attr['sixty'] = oldr.sixty
        for ii in range(1,6):
            seg = getattr(oldr, 'seg%d'%ii)
            if seg is not None and seg > 0:
                attr['seg%d'%ii] = seg

        if oldr.carid in remapcar:
            cur.execute("insert into runs values (%s, %s, %s, %s, %s, %s, %s, %s, %s, now())",
                (remapevent[oldr.eventid], remapcar[oldr.carid], oldr.course, oldr.run, oldr.cones, oldr.gates, oldr.raw, oldr.status, json.dumps(attr)))
        else:
            print("\t\tskipping unknown carid {}".format(oldr.carid))


    #SETTINGS
    print("\tsettings")
    settings = dict()
    for r in old.execute("select name,val from settings"):
        key = r['name']
        val = r['val']
        if key == 'useevents':
            key = 'dropevents'
        cur.execute("insert into settings values (%s, %s, now())", (key, val))

        
    #CHALLENGES (remap challengeid, eventid)
    print("\tchallenges")
    for r in old.execute("select * from challenges"):
        c = AttrWrapper(r, r.keys())

        newc = dict()
        newc['challengeid'] = uuid.uuid1()
        newc['eventid']     = remapevent[c.eventid]
        newc['name']        = c.name
        newc['depth']       = c.depth

        cur.execute("insert into challenges values (%s, %s, %s, %s, now())", (newc['challengeid'], newc['eventid'], newc['name'], newc['depth']))
        remapchallenge[c.id] = newc['challengeid']


    #CHALLENGEROUNDS (remap roundid, challengeid, carid)
    print("\tchallengerounds")
    check1 = set()
    for rp in old.execute("select * from challengerounds"):
        r = AttrWrapper(rp, rp.keys())
        cid  = remapchallenge[r.challengeid]
        c1id = remapcar[r.car1id]
        c2id = remapcar[r.car2id]
        ss = r.swappedstart and True or False
        c1d = r.car1dial or 0.0
        c2d = r.car2dial or 0.0
        check1.add((cid, r.round))
        cur.execute("insert into challengerounds values (%s, %s, %s, %s, %s, %s, %s, now())", (cid, r.round, ss, c1id, c1d, c2id, c2d))


    #CHALLENGERUNS (now in ther own table)
    print("\tchallengeruns")
    for r in challengeruns:
        chid  = remapchallenge[r.eventid >> 16]
        round = r.eventid & 0x0FFF
        caid  = remapcar[r.carid]
        if caid is not None and (chid, round) in check1:
            cur.execute("insert into challengeruns values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())", (chid, round, caid,
                            r.course, r.reaction, r.sixty, r.raw, r.cones, r.gates, r.status))

    if archive:
        global app
        with app.app_context():
            g.db = new
            g.seriestype = Series.ACTIVE
            g.series = name
            Result.cacheAll()
            cur.execute("DROP SCHEMA {} CASCADE".format(name))
            cur.execute("DELETE FROM drivers")
            cur.execute("DELETE FROM publiclog")
            cur.execute("DROP USER {}".format(name))

    old.close()
    new.commit()
    new.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: {} <db directory> <true/false>".format(sys.argv[0]))
    else:
        # Archive assumes that database is blank before we start this dog and pony show
        archive = sys.argv[2].lower() == 'true'
        print(glob.glob(sys.argv[1]))
        app = create_app()
        for f in glob.glob(sys.argv[1]):
            convert(f, archive)

