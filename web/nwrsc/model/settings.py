import logging
from flask import g

log = logging.getLogger(__name__)

class Settings(object):

    BOOLS  = ["superuniquenumbers", "indexafterpenalties", "usepospoints"]
    INTS   = ["largestcarnumber", "dropevents", "minevents"]
    STRS   = ["pospointlist", "seriesname", "classinglink", "resultsheader", "resultscss", "cardtemplate" ]
 
    def __init__(self, initial=None):
        self.superuniquenumbers = False
        self.indexafterpenalties = False
        self.usepospoints = False

        self.largestcarnumber = 1999
        self.dropevents = 2
        self.minevents = 0

        self.pospointlist = "20,16,13,11,9,7,6,5,4,3,2,1"
        self.seriesname = ""
        self.classinglink = ""
        self.resultsheader = ""
        self.resultscss = ""
        self.cardtemplate = ""

        if initial:
            self.__dict__.update(initial)

    def _obj2db(self, key, val):
        """ Convert from local data type to text column """
        if key in Settings.INTS:     return str(val)
        elif key in Settings.BOOLS:  return val and "1" or "0"
        return val

    def _db2obj(self, key, val):
        """ Convert from text columns to local data type """
        if key in Settings.INTS:    return int(val)
        elif key in Settings.BOOLS: return (val == "1")
        return val

    def save(self):
        with g.db.cursor() as cur:
            for k, v in self.getPublicFeed().items():
                strval = self._obj2db(k, v)
                cur.execute("INSERT INTO settings (name, val) VALUES (%s, %s) ON CONFLICT (name) DO UPDATE SET val=%s,modified=now()", (k, strval, strval))
        g.db.commit()

    @classmethod
    def get(cls):
        ret = Settings()
        with g.db.cursor() as cur:
            cur.execute("select * from settings")
            for row in cur.fetchall():
                setattr(ret, row['name'], ret._db2obj(row['name'], row['val']))
        return ret

    @classmethod
    def fromForm(cls, data):
        ret = Settings()
        for k in Settings.BOOLS + Settings.INTS + Settings.STRS:
            setattr(ret, k, getattr(data, k).data)
        return ret

    def getPublicFeed(self):
        """ Return a single level dict of the attributes and values to create a feed for this object """
        d = dict()
        for k,v in self.__dict__.items():
            if k[0] == '_' or v is None: continue
            d[k] = v
        return d


