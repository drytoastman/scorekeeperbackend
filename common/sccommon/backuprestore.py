import datetime
import operator
import os
import re
import subprocess
import sys
import zipfile

from google.cloud import storage

def backup_db(bucketname):
    dumpfile = datetime.date.today().strftime("scorekeeper-%Y-%m-%d.sql")
    with open(dumpfile, 'w') as dump:
        dump.write("UPDATE pg_database SET datallowconn = 'false' WHERE datname = 'scorekeeper';\n")
        dump.write("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'scorekeeper';\n")
        subprocess.run(["pg_dumpall", "-U", "postgres", "-c"], stdout=dump)
        dump.write("UPDATE pg_database SET datallowconn = 'true' WHERE datname = 'scorekeeper';\n")

    zipname = dumpfile+".zip"
    with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as zip:
        zip.write(dumpfile)
    os.remove(dumpfile)

    bucket  = storage.Client().get_bucket(bucketname)
    bucket.blob(zipname).upload_from_filename(zipname)
    os.remove(zipname)

def restore_db(bucketname):
    bucket = storage.Client().get_bucket(bucketname)

    # Find the latest file matching our filename pattern, download it and restore
    nmatch  = re.compile("scorekeeper-\S+.sql.zip")
    zipname = max(filter(lambda x: bool(nmatch.search(x.name)), bucket.list_blobs()), key=operator.attrgetter('time_created')).name
    bucket.blob(zipname).download_to_filename(zipname)

    dumpfile = zipname[:-4]
    with zipfile.ZipFile(zipname) as zip:
        zip.extract(dumpfile)
    subprocess.run(["psql", "-U", "postgres", "-f", dumpfile])
    os.remove(dumpfile)
    os.remove(zipname)

def restorecmd():
    restore_db(sys.argv[1])
