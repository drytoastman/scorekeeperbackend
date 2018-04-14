from collections import defaultdict
import logging
import operator
import re
import sys

from flask import g

from .base import AttrBase
from nwrsc.lib.encoding import to_json
from nwrsc.lib.misc import csvlist

log = logging.getLogger(__name__)

class Class(AttrBase):

    def getCountedRuns(self):
        if self.countedruns <= 0:
            return 999
        else:
            return self.countedruns

    @classmethod
    def empty(cls):
        return cls.fromForm(dict(classcode=''))

    @classmethod
    def fromForm(cls, data):
        ret = cls()
        ret.classcode       = data['classcode'] # This one MUST be there
        ret.descrip         = data.get('descrip', '')
        ret.indexcode       = data.get('indexcode', '')
        ret.caridxrestrict  = data.get('caridxrestrict', '')
        ret.classmultiplier = data.get('classmultiplier', 1.0)
        ret.carindexed      = data.get('carindexed',  False)
        ret.usecarflag      = data.get('usecarflag',  False)
        ret.eventtrophy     = data.get('eventtrophy', False)
        ret.champtrophy     = data.get('champtrophy', False)
        ret.secondruns      = data.get('secondruns',  False)
        ret.countedruns     = data.get('countedruns', 0)
        return ret
    
    @classmethod
    def get(cls, code):
        with g.db.cursor() as cur:
            cur.execute("select * from classlist where classcode=%s", (code,))
            return Class(**cur.fetchone())

    @classmethod
    def getAll(cls):
        with g.db.cursor() as cur:
            cur.execute("select * from classlist order by classcode")
            return [Class(**x) for x in cur.fetchall()]

    @classmethod
    def activeClasses(cls, eventid):
        with g.db.cursor() as cur:
            cur.execute("select distinct x.* from classlist as x, cars as c, runs as r where r.eventid=%s and r.carid=c.carid and c.classcode=x.classcode", (eventid,))
            active = [Class(**x) for x in cur.fetchall()]
            return sorted(active, key=lambda x:x.classcode)


class Index(AttrBase):

    @classmethod
    def empty(cls):
        return cls.fromForm(dict(indexcode=''))

    @classmethod
    def fromForm(cls, data):
        ret = cls()
        ret.indexcode = data['indexcode'] # This one MUST be there
        ret.descrip = data.get('descrip', '')
        ret.value = data.get('value', 1.0)
        return ret

    @classmethod
    def getAll(cls):
        with g.db.cursor() as cur:
            cur.execute("select * from indexlist order by indexcode")
            return [Index(**x) for x in cur.fetchall()]

    @classmethod
    def activeIndexes(cls):
        with g.db.cursor() as cur:
            cur.execute("select distinct indexcode from cars")
            return sorted([x[0] for x in cur.fetchall()])


class ClassData(object):

    def __init__(self, classdicts=[], indexdicts=[]):
        self.classlist = dict()
        self.indexlist = dict()
        for c in classdicts:
            self.classlist[c['classcode']] = Class(**c)
        for i in indexdicts:
            self.indexlist[i['indexcode']] = Index(**i)

    @classmethod
    def get(cls):
        """ Get all the class and index data for the active series """
        ret = ClassData()
        with g.db.cursor() as cur:
            cur.execute("select * from classlist")
            for x in cur.fetchall():
                c = Class(**x)
                ret.classlist[c.classcode] = c
            cur.execute("select * from indexlist")
            for x in cur.fetchall():
                i = Index(**x)
                ret.indexlist[i.indexcode] = i
        return ret


    def updateClassesTo(self, newclasses):
        """
            Delete and reinsert make it look like everything changed (modified times), so we make sure to only insert/delete what
            actually needs to happen.  Updates that don't change anything will get filtered at the plpgsql level
        """
        newcodes = set(newclasses.keys())
        oldcodes = set(self.classlist.keys())
        ignore   = set(['HOLD'])
        insert = newcodes - oldcodes - ignore
        update = newcodes & oldcodes - ignore
        delete = oldcodes - newcodes - ignore

        log.debug("%s %s %s", insert, update, delete)
        with g.db.cursor() as cur:
            for k in delete:
                cur.execute("DELETE from classlist where classcode=%s", (k,))
            for k in update:
                u = newclasses[k]
                cur.execute("UPDATE classlist SET descrip=%s, indexcode=%s, caridxrestrict=%s, classmultiplier=%s, carindexed=%s, usecarflag=%s, eventtrophy=%s, champtrophy=%s, secondruns=%s, countedruns=%s, modified=now() WHERE classcode=%s",
                                               (u.descrip,  u.indexcode,  u.caridxrestrict,  u.classmultiplier,  u.carindexed,  u.usecarflag,  u.eventtrophy,  u.champtrophy,  u.secondruns,  u.countedruns,  u.classcode))
            for k in insert:
                i = newclasses[k]
                cur.execute("INSERT INTO classlist (classcode, descrip, indexcode, caridxrestrict, classmultiplier, carindexed, usecarflag, eventtrophy, champtrophy, secondruns, countedruns, modified) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())",
                                              (i.classcode, i.descrip, i.indexcode, i.caridxrestrict, i.classmultiplier, i.carindexed, i.usecarflag, i.eventtrophy, i.champtrophy, i.secondruns, i.countedruns))
        g.db.commit()


    def updateIndexesTo(self, newindexes):
        """ Same deal as updateClassesTo but with Indexes instead """
        newcodes = set(newindexes.keys())
        oldcodes = set(self.indexlist.keys())
        ignore   = set([''])
        insert = newcodes - oldcodes - ignore
        update = newcodes & oldcodes - ignore
        delete = oldcodes - newcodes - ignore

        log.debug("%s %s %s", insert, update, delete)
        with g.db.cursor() as cur:
            for k in delete:
                cur.execute("DELETE from indexlist where indexcode=%s", (k,))
            for k in update:
                u = newindexes[k]
                cur.execute("UPDATE indexlist SET descrip=%s, value=%s, modified=now() WHERE indexcode=%s", (u.descrip,  u.value, u.indexcode))
            for k in insert:
                i = newindexes[k]
                cur.execute("INSERT INTO indexlist (indexcode, descrip, value, modified) VALUES (%s, %s, %s, now())", (i.indexcode, i.descrip, i.value))
        g.db.commit()


    def indexes(self):
        ret = list(self.indexlist.keys())
        ret.remove("")
        return sorted(ret)


    def restrictedRegistrationIndexes(self, classcode):
        RINDEX = re.compile(r'([+-])\((.*?)\)')
        return self._restrictedList(classcode, RINDEX)

    def restrictedClassMultiplierIndexes(self, classcode):
        RMULT = re.compile(r'([+-])\[(.*?)\]')
        return self._restrictedList(classcode, RMULT)

    def _restrictedList(self, classcode, regex):

        def globItem(item, full):
            tomatch = '^' + item.strip().replace('*', '.*') + '$'
            ret = set()
            for x in full:
                if re.search(tomatch, x):
                    ret.add(x)
            return ret

        def processList(results, fullset):
            ret = set(fullset)
            for ii, pair in enumerate(results):
                if pair[0] not in ('+','-'):
                    log.warning("Index limit script: excepted + or -, found {}".format(pair[0]))
                    continue
                ADD = (pair[0] == '+')
                if ii == 0 and ADD:
                    ret = set()
                for item in csvlist(pair[1]):
                    if ADD:
                        ret |= globItem(item, fullset)
                    else:
                        ret -= globItem(item, fullset)
            return ret

        if classcode not in self.classlist or not self.classlist[classcode].carindexed:
            return []

        idxlist = self.indexes()
        if not self.classlist[classcode].caridxrestrict:
            return idxlist

        args = self.classlist[classcode].caridxrestrict.replace(" ", "")
        restrict = processList(regex.findall(args), idxlist)
        if len(restrict) == len(idxlist):
            restrict = []
        return restrict


    def getCountedRuns(self, classcode):
        try:
            return self.classlist[classcode].getCountedRuns()
        except:
            return 999


    def getEffectiveIndex(self, car): 
        indexval = 1.0
        indexstr = ""
        try:
            cls = self.classlist[car.classcode]

            if cls.indexcode != "":
                indexval *= self.indexlist[cls.indexcode].value
                indexstr  = cls.indexcode

            if cls.carindexed and car.indexcode:
                indexval *= self.indexlist[car.indexcode].value
                indexstr  = car.indexcode

            if cls.classmultiplier < 1.000:
                restrict = self.restrictedClassMultiplierIndexes(car.classcode)
                if car.indexcode in restrict and (not cls.usecarflag or car.useclsmult):
                    indexval *= cls.classmultiplier
                    indexstr = indexstr + '*'

        except Exception as e:
            log.warning("getEffectiveIndex(%s,%s,%s) failed: %s" % (car.classcode, car.indexcode, car.useclsmult, e))

        return (indexval, indexstr)


    def getJSONArrays(self):
        classes = dict()
        indexes = dict()
        for k, v in sorted(self.classlist.items()):
            r = self.restrictedRegistrationIndexes(k)
            m = self.restrictedClassMultiplierIndexes(k)
            classes[k] = { 'isindexed': v.carindexed, 'usecarflag': v.usecarflag, 'idxrestrict': r, 'multrestrict': m }
        for k, v in sorted(self.indexlist.items()):
            indexes[k] = v.descrip
        return to_json(classes), to_json(indexes)

