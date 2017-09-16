import json
import logging
from flask import g

TABLES = ['drivers', 'cars', 'events']
COLUMNS       = dict()
PRIMARY_KEYS  = dict()
NONPRIMARY    = dict()
UPDATES       = dict()
INSERTS       = dict()

log = logging.getLogger(__name__)

class AttrBase(object):

    @classmethod
    def initialize(cls):
        """ A little introspection to load the schema from database """
        with g.db.cursor() as cur:
            # Need to set a valid series so we can inspect the format
            cur.execute("SELECT schema_name FROM information_schema.schemata")
            serieslist = set([x[0] for x in cur.fetchall() if not x[0].startswith('pg_') and x[0] not in ('information_schema', 'public')])
            if not len(serieslist):
                raise Exception("No valid series yet, need to get this to restart somehow")

            testseries = (serieslist.pop(), 'public')
            cur.execute("set search_path=%s,%s", testseries)

            # Determing the primary keys for each table
            for table in TABLES:
                cur.execute("SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)" \
                            "WHERE i.indrelid = '{}'::regclass AND i.indisprimary".format(table))
                PRIMARY_KEYS[table] = [row[0] for row in cur.fetchall()]

                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s AND table_schema IN %s AND column_name NOT IN ('modified', 'username', 'password')", (table, testseries))
                COLUMNS[table] = [row[0] for row in cur.fetchall()]
                NONPRIMARY[table] = list(set(COLUMNS[table]) - set(PRIMARY_KEYS[table]))

                UPDATES[table] = "UPDATE {} SET {},modified=now() WHERE {}".format(table, ", ".join("{}=%({})s".format(k,k) for k in NONPRIMARY[table]), " AND ".join("{}=%({})s".format(k, k) for k in PRIMARY_KEYS[table]))
                INSERTS[table] = "INSERT INTO {} ({},modified) VALUES ({}, now())".format(table, ",".join(COLUMNS[table]), ",".join(["%({})s".format(x) for x in COLUMNS[table]]))


    def __init__(self, **kwargs):
        self.attr = dict()
        self._merge(**kwargs)

    def insert(self):
        with g.db.cursor() as cur:
            self.cleanAttr()
            cur.execute(INSERTS[self.TABLENAME], self.__dict__)
            g.db.commit()

    def update(self):
        with g.db.cursor() as cur:
            self.cleanAttr()
            cur.execute(UPDATES[self.TABLENAME], self.__dict__)
            g.db.commit()

    @property
    def columns(self):
        return COLUMNS[self.TABLENAME]

    @classmethod
    def getval(cls, sql, args=None):
        with g.db.cursor() as cur:
            cur.execute(sql, args)
            if cur.rowcount == 1:
                return cur.fetchone()[0]
            return None

    @classmethod
    def getunique(cls, sql, args=None):
        with g.db.cursor() as cur:
            cur.execute(sql, args)
            assert(cur.rowcount <= 1) # If we get multiple, postgresql primary key indexing failed
            return cur.rowcount == 1 and cls(**cur.fetchone()) or None

    @classmethod
    def getall(cls, sql, args=None):
        with g.db.cursor() as cur:
            cur.execute(sql, args)
            return [cls(**x) for x in cur.fetchall()]

    def _merge(self, **kwargs):
        """ Merge these values into this object, attr gets merged with the attr dict """
        for k, v in kwargs.items():
            if k == 'attr':
                self.attr.update(v)
            else:
                setattr(self, k, v)

    def cleanAttr(self):
        """ Remove nulls, blanks, zeros, etc to reduce attr size """
        if hasattr(self, 'attr'):
            for k in list(self.attr.keys()):
                v = self.attr[k]
                if v is None or \
                  type(v) is str and v.strip() == "" or \
                  type(v) is int and v == 0 or \
                  type(v) is float and v <= 0.0 or \
                  type(v) is bool and not v:
                    del self.attr[k]

    def feedFilter(self, key, value):
        """ Override this function to filter our things that shouldn't end up in the public json/xml feed """
        return value

    def getPublicFeed(self):
        """ Return a single level dict of the attributes and values to create a feed for this object """
        d = dict()
        self.cleanAttr()
        for k,v in {**self.__dict__, **self.attr}.items():
            if k[0] == '_' or k == 'attr':
                continue
            v = self.feedFilter(k, v)
            if v is None:
                continue
            d[k] = v
        return d

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self.__dict__)


class Entrant(AttrBase):
    """ Generic holder for some subset of driver and car entry data """
    def __repr__(self):
        return "Entrant ({} {})".format(self.firstname or 'Missing', self.lastname or 'Missing')

    def __getattr__(self, k):
        return " "

