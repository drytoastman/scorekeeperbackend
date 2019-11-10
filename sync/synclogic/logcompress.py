import operator
import psycopg2

from .model import DataInterface
from .objects import row2json

def compress_logtables():
    DataInterface.initialize(6432)
    with DataInterface.connectLocal(6432) as db:
        with db.cursor() as cur:
            print("public")
            objs = list()
            for t in DataInterface.PUBLIC_TABLES + ['version']:
                collect_table(cur, t, objs)
            write_log(cur, 'publiclog', objs)

            for s in DataInterface.seriesList(db):
                print(s)
                cur.execute("set search_path=%s", (s,))
                objs = list()
                for t in set(DataInterface.ALL_TABLES) - set(DataInterface.PUBLIC_TABLES):
                    collect_table(cur, t, objs)
                write_log(cur, 'serieslog', objs)

        db.commit()

def collect_table(cur, table, objs):
    cur.execute("select * from {} order by modified".format(table))
    for row in cur.fetchall():
        jrow = row2json(row)
        objs.append({ 'tablename': table,
                          'otime': jrow.get('modified'),
                          'ltime': jrow.get('modified'),
                        'objjson': jrow
                     })

def write_log(cur, logtable, objs):
    cur.execute("DELETE FROM {}".format(logtable))
    sql = "INSERT INTO {} VALUES(default, 'compress', 'compress', %(tablename)s, 'I', %(otime)s, %(ltime)s, '{{}}', %(objjson)s)".format(logtable)
    objs.sort(key=operator.itemgetter('otime'))
    psycopg2.extras.execute_batch(cur, sql, objs)
    print("{} {} objs".format(logtable, len(objs)))
