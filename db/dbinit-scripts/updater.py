#!/usr/bin/env python3

import psycopg2

LOCALARGS = {
            "host": "127.0.0.1",
            "port": 6432,
            "user": "postgres",
          "dbname": "scorekeeper",
"application_name": "schemaupdate"
}

updatelist = [
    (True, "ALTER TABLE events ADD COLUMN accountid TEXT REFERENCES paymentaccounts"),
    (True, "UPDATE events SET accountid=attr->'payments'"),
    "20171010"
]

def get_version(db):
    with db.cursor() as cur:
        cur.execute("SELECT version FROM version")
        if cur.rowcount < 1:
            return None
        if cur.rowcount == 1:
            return cur.fetchone()[0]
        raise Exception("More than one version in a table that should be constrained to 1 row")

def locate_start(ver):
    try:
        return updatelist.index(ver) + 1
    except:
        return 0

def get_series(db):
    with db.cursor() as cur:
        cur.execute("SELECT schema_name FROM information_schema.schemata")
        return set([x[0] for x in cur.fetchall() if not x[0].startswith('pg_') and x[0] not in ('information_schema', 'public')])

def set_version(db, ver):
    with db.cursor() as cur:
        print("set version to {}".format(ver))
        cur.execute("UPDATE version SET version=%s", (ver,))

if __name__ == "__main__":
    with psycopg2.connect(**LOCALARGS) as db:
        with db.cursor() as cur:
            series = get_series(db)
            start = locate_start(get_version(db))
            for cmd in updatelist[start:]:
                if isinstance(cmd, tuple):
                    print(cmd[1])
                    # True = Execute same update for all series schema, False = just once for public schema
                    if cmd[0]: 
                        for s in series:  
                            cur.execute("set search_path=%s,%s", (s, 'public'))
                            cur.execute(cmd[1])
                    else:
                        cur.execute(cmd[1])
                else:
                    set_version(db, cmd)
        db.commit()

