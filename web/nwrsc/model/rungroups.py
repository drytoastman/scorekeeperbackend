from collections import defaultdict, OrderedDict
from operator import attrgetter
from flask import g
from .base import Entrant


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

class GroupOrder(OrderedDict):
    """
        List of classes in a rungroup
        Maps from classcode to a ClassList (list of Entrants for that class)
    """
    def pad(self):
        """ If the class is a odd # of entries and next class is not single, add a space """
        codes = list(self.keys())
        for ii in range(len(codes)-1):
            if len(self[codes[ii]]) % 2 != 0 and len(self[codes[ii+1]]) > 1:
                self[codes[ii]].append(Entrant())

    def number(self):
        """ Create the grid numbers for each entry """
        ii = 0
        for code in self:
            for e in self[code]:
                ii += 1
                e.grid = ii

    @property
    def count(self):
        return sum(len(x) for x in self.values())
        

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
                for row, cls in enumerate(classes):
                    if group == 0:
                        cur.execute("DELETE FROM classorder WHERE eventid=%s AND classcode=%s", (eventid, cls))
                        continue
                    (fg,fr) = self.find(cls)
                    if fg == 0:
                        cur.execute("INSERT INTO classorder (eventid, classcode, rungroup, gorder, modified) VALUES (%s,%s,%s,%s,now())", (eventid, cls, group, row))
                    elif group != fg or row != fr:
                        cur.execute("UPDATE classorder SET rungroup=%s, gorder=%s, modified=now() WHERE eventid=%s AND classcode=%s", (group, row, eventid, cls))
            g.db.commit()

    @classmethod
    def getForEvent(cls, eventid):
        ret = RunGroups(GroupOrder)
        with g.db.cursor() as cur:
            cur.execute("SELECT * FROM classorder WHERE eventid=%s ORDER BY rungroup, gorder", (eventid,))
            active = ['HOLD']
            for x in cur.fetchall():
                active.append(x['classcode'])
                ret[x['rungroup']][x['classcode']] = ClassList()
                ret[x['rungroup']+100][x['classcode']] = ClassList()
            cur.execute("SELECT classcode FROM classlist WHERE classcode NOT IN %s ORDER BY classcode", (tuple(active),))
            for x in cur.fetchall():
                ret[0][x[0]] = ClassList()
                ret[100][x[0]] = ClassList()
        return ret

