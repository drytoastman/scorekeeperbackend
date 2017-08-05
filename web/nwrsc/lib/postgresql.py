import pkg_resources
import psycopg2

def check_password(host, port, user, password):
    try:
        pg = psycopg2.connect(host=host, port=port, user=user, password=password, dbname='scorekeeper')
        pg.close()
        return True
    except Exception:
        return False


def ensure_series_schema(host, port, seriesname, seriespass):
    db = psycopg2.connect(host=host, port=port, user=user, password=password, dbname='scorekeeper')
    dbc = db.cursor()
    dbc.execute("SELECT tablename FROM pg_tables WHERE schemaname=%s AND tablename='runs'", (seriesname,))
    if dbc.rowcount == 0:
        print("Creating series tables")
        dbc.execute(processsqlfile('series.sql', { '<seriesname>':seriesname, '<password>':seriespass }))
        db.commit()
    db.close()


def processsqlfile(name, replacements):
    ret = []
    with pkg_resources.resource_stream('nwrsc', 'model/'+name) as ip:
        for l in ip.readlines():
            l = l.decode('utf-8')
            for key in replacements:
                l = l.replace(key, replacements[key])
            ret.append(l)
    return '\n'.join(ret)

