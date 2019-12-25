import logging
import psycopg2 
import psycopg2.extras

from flask import g

TABLES = ['drivers', 'cars', 'events', 'paymentaccounts', 'paymentitems', 'paymentsecrets', 'registered', 'payments', 'externalresults' ]
COLUMNS       = dict()
PRIMARY_KEYS  = dict()
NONPRIMARY    = dict()
UPDATES       = dict()
INSERTS       = dict()
UPSERTS       = dict()
DELETES       = dict()

log = logging.getLogger(__name__)

# setup uuid for postgresql
psycopg2.extras.register_uuid()
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

def whereprimary(table):
    return " AND ".join("{}=%({})s".format(k, k) for k in PRIMARY_KEYS[table])

def setnonprimary(table):
    return ", ".join("{}=%({})s".format(k,k) for k in NONPRIMARY[table])

def columnlist(table):
    return ",".join(COLUMNS[table])

def primarylist(table):
    return ",".join(PRIMARY_KEYS[table])

def insertcolumns(table):
    return ",".join("%({})s".format(x) for x in COLUMNS[table])



class AttrBase(object):

    @classmethod
    def connect(cls, host, port, user, app='webserver', autocommit=False):
        db = psycopg2.connect(cursor_factory=psycopg2.extras.DictCursor, application_name=app, dbname="scorekeeper", host=host, port=port, user=user)
        db.autocommit = autocommit
        return db


    @classmethod
    def changelistener(cls, host, port, user, callback):
        import select
        db = cls.connect(host, port, user, app='changelistener', autocommit=True)
        with db.cursor() as cur:
            cur.execute("LISTEN datachange;")
            while True:
                if select.select([db],[],[],5) == ([],[],[]):
                    pass
                else:
                    db.poll()
                    while db.notifies:
                        notify = db.notifies.pop(0)
                        callback(notify.payload) # payload is the table name


    @classmethod
    def initialize(cls, host, port):
        """ A little introspection to load the schema from database """
        with cls.connect(host=host, port=port, user="localuser") as db:
            with db.cursor() as cur:
                testseries = ('template', 'public')
                cur.execute("set search_path=%s,%s", testseries)

                # Determing the primary keys for each table
                for table in TABLES:
                    cur.execute("SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)" \
                                "WHERE i.indrelid = '{}'::regclass AND i.indisprimary".format(table))
                    PRIMARY_KEYS[table] = [row[0] for row in cur.fetchall()]

                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s AND table_schema IN %s AND column_name NOT IN ('created', 'modified', 'username', 'password')", (table, testseries))
                    
                    COLUMNS[table] = [row[0] for row in cur.fetchall()]
                    NONPRIMARY[table] = list(set(COLUMNS[table]) - set(PRIMARY_KEYS[table]))

                    DELETES[table] = "DELETE FROM {} WHERE {}".format(table, whereprimary(table))
                    UPDATES[table] = "UPDATE {} SET {},modified=now() WHERE {}".format(table, setnonprimary(table), whereprimary(table))
                    INSERTS[table] = "INSERT INTO {} ({},modified) VALUES ({}, now())".format(table, columnlist(table), insertcolumns(table)) 
                    UPSERTS[table] = "INSERT INTO {} ({},modified) VALUES ({}, now()) ON CONFLICT ({}) DO UPDATE SET {},modified=now()".format(
                                                    table, 
                                                    columnlist(table),
                                                    insertcolumns(table),
                                                    primarylist(table),
                                                    setnonprimary(table))


    def __init__(self, **kwargs):
        self.attr = dict()
        self._merge(**kwargs)

    def insert(self):
        with g.db.cursor() as cur:
            self.cleanAttr()
            self.fillMissing()
            cur.execute(INSERTS[self.TABLENAME], self.__dict__)
            g.db.commit()

    def upsert(self):
        with g.db.cursor() as cur:
            self.cleanAttr()
            cur.execute(UPSERTS[self.TABLENAME], self.__dict__)
            g.db.commit()

    def update(self):
        with g.db.cursor() as cur:
            self.cleanAttr()
            cur.execute(UPDATES[self.TABLENAME], self.__dict__)
            g.db.commit()

    def delete(self):
        with g.db.cursor() as cur:
            cur.execute(DELETES[self.TABLENAME], self.__dict__)
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

    def fillMissing(self):
        for name in self.columns:
            if not hasattr(self, name):
                setattr(self, name, None)

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

    def getAsDict(self):
        """ Return a single level dict of the attributes and values to create a feed for this object """
        d = dict()
        self.cleanAttr()
        for k,v in {**self.__dict__, **self.attr}.items():
            if k[0] == '_' or k == 'attr':
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

