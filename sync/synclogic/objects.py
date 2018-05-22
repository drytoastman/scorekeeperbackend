from collections import namedtuple
import datetime
import logging
import operator
import random
import uuid

log  = logging.getLogger(__name__)

from synclogic.model import DataInterface

def pkfromjson(table, data):
    """
        JSON logs will store UUID as text, use this to turn them back into UUID's when parsing,
        but only if the column was originally UUID.  Otherwise text columns with a UUID like string
        will get converted as well which is incorrect.
    """
    return tuple([ptype=='uuid' and uuid.UUID(data[k]) or data[k] for k,ptype in DataInterface.PRIMARY_KEYS[table].items()])

InsertObject = namedtuple('InsertObject', 'otime, data')
UpdateObject = namedtuple('UpdateObject', 'otime, odiff, adiff, adel')

class LoggedObject():
    """ An object loaded from the log data insert and following updates across multiple machines """

    def __init__(self, table, pk):
        self.table   = table
        self.pk      = pk
        self.initA   = None
        self.initB   = None
        self.updates = []

    def insert(self, otime, newdata):
        if 'created' not in newdata:
            # HACK: fix for missing columns
            newdata['created'] = "1970-01-01T00:00:00"
        if not self.initA:
            self.initA = InsertObject(otime, newdata)
            return
        if not self.initB:
            self.initB = InsertObject(otime, newdata)
            return

        raise Exception("inserted thrice?")

    def _diffobj(self, data1, data2):
        attr1 = data1.pop('attr', dict())
        attr2 = data2.pop('attr', dict())
        odiff = dict(set(data2.items()) - set(data1.items()))  # Differences in object columns
        adiff = dict(set(attr2.items()) - set(attr1.items()))  # Additions/Differences in attr
        adel  = attr1.keys() - attr2.keys()                    # Attr keys that were deleted
        return (odiff, adiff, adel)

    def _issame(self, data1, data2):
        (odiff, adiff, adel) = self._diffobj(data1, data2)
        return not odiff and not adiff and not adel

    def update(self, time, olddata, newdata):
        (odiff, adiff, adel) = self._diffobj(olddata, newdata)
        self.updates.append(UpdateObject(time, odiff, adiff, adel))

    def _convert2logformat(self, dbobj):
        # Convert psycopg2 data into something we can compare with JSON logs
        compare = dict()
        for k in dbobj.keys():
            data = dbobj[k]
            if k == 'attr':
                compare['attr'] = data
            elif type(data) is datetime.datetime:
                compare[k] = data.isoformat().strip('0')
            elif type(data) is uuid.UUID:
                compare[k] = str(data)
            else:
                compare[k] = data
        return compare

    def finalize(self, last):
        # Later insert becomes an update to catch any potential changes outside our purview
        if self.initA.otime < self.initB.otime:
            data = self.initA.data.copy()
            self.update(self.initB.otime, self.initA.data, self.initB.data)
        else:
            data = self.initB.data.copy()
            self.update(self.initA.otime, self.initB.data, self.initA.data)

        # And rebuild the object with all of the updates
        for uobj in sorted(self.updates, key=operator.attrgetter('otime')):
            data.update(uobj.odiff)
            data['attr'].update(uobj.adiff)
            for key in uobj.adel:
                data['attr'].pop(key, None)

            # HACK: change old logged membership to barcode, if there hasn't been a barcode change since the schema move
            if 'barcode' not in data:
                data['barcode'] = data['membership']


        # Pick modified time based on object that didn't change or the final modtime + epsilon
        both = False
        if not self._issame(self._convert2logformat(last.data), dict(data.items())):
            both = True
            data['modified'] = (datetime.datetime.strptime(data['modified'], "%Y-%m-%dT%H:%M:%S.%f") + datetime.timedelta(microseconds=1)).isoformat()
        return PresentObject(self.table, self.pk, data), both


    @classmethod
    def loadFrom(cls, objdict, db, pkset, src, table, when):
        with db.cursor() as cur:
            cur.execute("SELECT * FROM {} WHERE tablen=%s and otime>=%s ORDER BY otime".format(src), (table, when))
            for obj in cur.fetchall():

                def tryuuid(txt):
                    try: return uuid.UUID(txt)
                    except: return txt

                if obj['action'] == 'I':
                    pk = pkfromjson(table, obj['newdata'])
                    if pk not in objdict and pk in pkset:
                        objdict[pk] = LoggedObject(table, pk)
                    if pk in objdict:
                        objdict[pk].insert(obj['otime'], obj['newdata'])

                elif obj['action'] == 'U':
                    pk = pkfromjson(table, obj['newdata'])
                    if pk in objdict:
                        objdict[pk].update(obj['otime'], obj['olddata'], obj['newdata'])

                elif obj['action'] == 'D':
                    pk = pkfromjson(table, obj['olddata'])
                    if pk in objdict:
                        raise Exception("LoggedObject delete is invalid")

                else:
                    log.warning("How did we get here?")



class PresentObject():

    def __init__(self, table, pk, data):
        self.table = table
        self.pk = pk
        self.data = data
        self.modified = data['modified']
        self.created = data.get('created', None)

    def __repr__(self):
        return "PresentObject ({}, {}, {})".format(self.table, self.pk, self.data)

    @classmethod
    def minmodtime(cls, d):
        if len(d) == 0:
            return datetime.datetime(2017, 1, 1)
        return min([v.modified for v in d.values()])

    @classmethod
    def mincreatetime(cls, *lists):
        mintime = datetime.datetime(9999, 1, 1)
        for l in lists:
            if len(l):
                mintime = min(mintime, min([v.created for v in l]))
        return mintime

    @classmethod
    def loadPresent(cls, db, table):
        assert table in DataInterface.TABLE_ORDER, "No such table {}".format(table)
        ret = dict()
        with db.cursor() as cur:
            cur.execute("SELECT * from {}".format(table))
            for row in cur.fetchall():
                pk = tuple([row[k] for k in DataInterface.PRIMARY_KEYS[table]])
                ret[pk] = cls(table, pk, row)
        return ret


# For storage and query of recently deleted objects
class DeletedObject():

    def __init__(self, table, pk, data, deletedat):
        self.table = table
        self.pk = pk
        self.data = data
        self.deletedat = deletedat

    @classmethod
    def deletedSince(cls, db, table, when):
        assert table in DataInterface.TABLE_ORDER, "No such table {}".format(table)
        ret = dict()

        with db.cursor() as cur:
            cur.execute("SELECT otime, olddata FROM {} WHERE action='D' AND tablen=%s AND otime>%s".format(DataInterface.logtablefor(table)), (table, when,))
            for row in cur.fetchall():
                pk = pkfromjson(table, row['olddata'])
                ret[pk] = cls(table, pk, row['olddata'], row['otime'])
        return ret

