import bisect
from collections import defaultdict, OrderedDict
import logging
from operator import attrgetter
import types

from flask import g
from .base import AttrBase, Entrant

log = logging.getLogger(__name__)

class ClassList(list):
    """ List of entries for this particular run group position """
    def __init__(self):
        list.__init__(self)
        self.numbers = set()

    def add(self, e):
        if (e.number+100)%200 in self.numbers: return False
        self.append(e)
        self.numbers.add(e.number)
        return True

    @property
    def truecount(self):
        """ Count of real entrants, skipping blank pads """
        return len(list(filter(lambda x: x.number, self)))


class GroupOrder(OrderedDict):
    """
        List of classes in a rungroup
        Maps from classcode to a ClassList (list of Entrants for that class)
    """
    def pad(self):
        """ If the class is a odd # of entries and next class is not single, add a space """
        codes = list(self.keys())
        rows = 0
        for ii in range(len(codes)-1):
            cl = self[codes[ii]]
            clnext = self[codes[ii+1]]
            rows += len(cl)
            if rows % 2 != 0 and len(clnext) > 1:
                cl.append(Entrant())
                rows += 1

    def number(self):
        """ Create the grid numbers for each entry """
        ii = 0
        for code in self:
            for e in self[code]:
                ii += 1
                e.grid = ii

    @property
    def count(self):
        """ count of entrants in this rungroup """
        return sum(x.truecount for x in self.values())


class RunGroups(defaultdict):
    """
        The list of all rungroups for the event
        Maps from a group number to a GroupOrder (keys = 1, 2 .. and 101, 102 ...)
    """
    def put(self, entrant):
        cc = entrant.classcode
        for num, go in self.items():
            if cc in go:
                if not go[cc].add(entrant):
                    self[num+100][cc].add(entrant)
                return
        raise Exception("Failed to find a rungroup for {}".format(cc))

    def asjson(self):
        ret = {}
        for num,go in self.items():
            ret[num] = list()
            for cls,entries in go.items():
                for e in entries:
                    ret[num].append({"carid": e.carid, "grid": e.grid, "name": e.firstname + " " + e.lastname, "net": e.net, "number": e.number, "classcode": e.classcode })
        return ret

    def sort(self, key):
        for go in self.values():
            for clist in go.values():
                clist.sort(key=attrgetter(key))

    def find(self, cls):
        for group, go in self.items():
            if cls in go:
                return (group, list(go.keys()).index(cls))
        return (0, 0)

    def update(self, eventid, newgroups):
        with g.db.cursor() as cur:
            for group, classes in newgroups.items():
                log.debug("{}, {}".format(group, classes))
                if group == 0:
                    continue
                cur.execute("INSERT INTO classorder (eventid, rungroup, classes, modified) VALUES (%s, %s, %s, now()) ON CONFLICT (eventid, rungroup) DO UPDATE SET classes=%s, modified=now()",
                            (eventid, group, classes, classes))
            g.db.commit()

    @classmethod
    def getForEvent(cls, eventid):
        ret = RunGroups(GroupOrder)
        for ii in range(1,4):
            ret[ii]
            ret[100+ii]

        with g.db.cursor() as cur:
            cur.execute("SELECT rungroup,classes FROM classorder WHERE eventid=%s ORDER BY rungroup", (eventid,))
            active = []
            for row in cur.fetchall():
                group = row['rungroup']
                for code in row['classes']:
                    active.append(code)
                    ret[group][code]     = ClassList()
                    ret[group+100][code] = ClassList()

            cur.execute("SELECT classcode FROM classlist {} ORDER BY classcode".format(active and "WHERE classcode NOT IN %s" or ""), (tuple(active),))
            for x in cur.fetchall():
                ret[0][x[0]] = ClassList()
                ret[100][x[0]] = ClassList()
        return ret


class RunOrder(AttrBase):

    @classmethod
    def getNextRunOrder(cls, carid, eventid, course, rungroup):
        """ Returns a list of objects (classcode, carid) for the next cars in order after carid """
        with g.db.cursor() as cur:
            cur.execute("SELECT unnest(cars) cid from runorder WHERE eventid=%s AND course=%s AND rungroup=%s", (eventid, course, rungroup))
            order = [x[0] for x in cur.fetchall()]
            ret = []
            for ii, rowcarid in enumerate(order):
                if rowcarid == carid:
                    for jj in range(ii+1, ii+4)[:len(order)-1]:  # get next 3 but only to length of list (no repeats)
                        cur.execute("SELECT c.carid,c.classcode,c.number from cars c WHERE carid=%s", (order[jj%len(order)], ))
                        ret.append(RunOrder(**cur.fetchone()))
                    break
            return ret



    @classmethod
    def getProGroupings(cls, eventid, rungroup):
        """ Best effort to deduce what current runorder groupings exists by comparing runorder on the two courses """

        def process(order, other):
            cap = 0
            ret = list()
            for ii, e in enumerate(order):
                try:
                    off = other.index(e) - ii
                    if off > 0 and cap <= 0:  # transition to being ahead in opposite course tells all, start of group
                        ret.append(ii)
                    cap = off
                except ValueError:
                    pass
            return ret


        with g.db.cursor() as cur:
            cur.execute("SELECT unnest(cars) cid from runorder WHERE eventid=%s AND course=%s AND rungroup=%s", (eventid, 1, rungroup))
            leftorder  = [x[0] for x in cur.fetchall()]

            cur.execute("SELECT unnest(cars) cid from runorder WHERE eventid=%s AND course=%s AND rungroup=%s", (eventid, 2, rungroup))
            rightorder = [x[0] for x in cur.fetchall()]

            return types.SimpleNamespace(left=leftorder, right=rightorder, leftgroup=process(leftorder, rightorder), rightgroup=process(rightorder, leftorder))



    @classmethod
    def getNextRunOrderPro(cls, carid, eventid, course, rungroup, run):
        """ Returns a list of objects (classcode, carid) for the next cars in order after carid """

        with g.db.cursor() as cur:
            pro = cls.getProGroupings(eventid, rungroup)

            if course == 1:
                order = pro.left
                group = pro.leftgroup
            else:
                order = pro.right
                group = pro.rightgroup

            ret = []
            for ii, cid in enumerate(order):
                if cid == carid:
                    if run%2 > 0: # odd run, wrap inside our little subgroup
                        bi    = bisect.bisect(group, ii)
                        start = group[bi-1]
                        end   = group[bi]
                    else:
                        start = 0 # full list
                        end   = len(order)

                    for jj in range(ii+1, ii+4):
                        if jj >= end:
                            jj = jj - (end - start)
                        cur.execute("SELECT c.carid,c.classcode,c.number from cars c WHERE carid=%s", (order[jj], ))
                        ret.append(RunOrder(**cur.fetchone()))
                    break
            return ret
