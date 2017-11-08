import logging
from flask import g

log = logging.getLogger(__name__)

class Settings(object):

    DEFAULTS = {
        "superuniquenumbers":   False,
        "indexafterpenalties":  False,
        "usepospoints":         False,
        "largestcarnumber":     1999,
        "dropevents":           2,
        "minevents":            0,
        "pospointlist":         "20,16,13,11,9,7,6,5,4,3,2,1",
        "seriesname":           "",
        "classinglink":         "",
        "resultsheader":        "",
        "resultscss":           "",
        "cardtemplate":         ""
    }
 
    def __init__(self, initial = None):
        for k, v in Settings.DEFAULTS.items():
            setattr(self, k, v)
        if initial:
            self.__dict__.update(initial)

    def _obj2db(self, key, val):
        """ Convert from local data type to text column """
        if key not in Settings.DEFAULTS:               return val
        elif isinstance(Settings.DEFAULTS[key], bool): return val and "1" or "0"
        elif isinstance(Settings.DEFAULTS[key], int):  return str(val)
        else:                                          return val

    @classmethod
    def _db2obj(cls, key, val):
        """ Convert from text columns to local data type """
        if key not in Settings.DEFAULTS:               return val
        elif isinstance(Settings.DEFAULTS[key], bool): return (val == "1")
        elif isinstance(Settings.DEFAULTS[key], int):  return int(val)
        else:                                          return val

    def save(self):
        with g.db.cursor() as cur:
            for k, v in self.getPublicFeed().items():
                strval = self._obj2db(k, v)
                cur.execute("INSERT INTO settings (name, val) VALUES (%s, %s) ON CONFLICT (name) DO UPDATE SET val=%s,modified=now()", (k, strval, strval))
        g.db.commit()

    def getPublicFeed(self):
        """ Return a single level dict of the attributes and values to create a feed for this object """
        d = dict()
        for k,v in self.__dict__.items():
            if k not in Settings.DEFAULTS: continue
            d[k] = v
        return d

    @classmethod
    def get(cls, name):
        with g.db.cursor() as cur:
            cur.execute("select val from settings where name=%s", (name, ))
            row = cur.fetchone()
            if row:
                return Settings._db2obj(name, row['val'])
            else:
                return Settings.DEFAULTS[name]

    @classmethod
    def getAll(cls):
        ret = Settings()
        with g.db.cursor() as cur:
            cur.execute("select * from settings")
            for row in cur.fetchall():
                setattr(ret, row['name'], ret._db2obj(row['name'], row['val']))
        return ret

    @classmethod
    def fromForm(cls, data):
        ret = Settings()
        for k in Settings.DEFAULTS:
            setattr(ret, k, getattr(data, k).data)
        return ret

