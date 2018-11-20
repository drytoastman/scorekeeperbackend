#!/usr/bin/env python3

# pip3 install --upgrade google-cloud-storage

import argparse
import datetime
import operator
import os
import re
import subprocess
import sys
import zipfile

from google.cloud import storage
from google.cloud.storage import Blob

def dumpdb():
    dumpfile = datetime.date.today().strftime("scorekeeper-%Y-%m-%d.sql")
    with open(dumpfile, 'w') as dump:
        dump.write("UPDATE pg_database SET datallowconn = 'false' WHERE datname = 'scorekeeper';\n")
        dump.write("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'scorekeeper';\n")
        subprocess.run(["pg_dumpall", "-h", "127.0.0.1", "-p", "6432", "-U", "postgres", "-c"], stdout=dump)
        dump.write("UPDATE pg_database SET datallowconn = 'true' WHERE datname = 'scorekeeper';\n")

    zipname = dumpfile+".zip"
    with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as zip:
        zip.write(dumpfile)

    os.remove(dumpfile)
    return zipname


def restoredb(zipname):
    dumpfile = zipname[:-4]
    with zipfile.ZipFile(zipname) as zip:
        zip.extract(dumpfile)
    subprocess.run(["psql", "-h", "127.0.0.1", "-p", "6432", "-U", "postgres", "-f", dumpfile])
    os.remove(dumpfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Interact with Google Cloud Backup')
    parser.add_argument('--local',    action='store_true', help='backup the scorekeeper database to a local file')
    parser.add_argument('--backup',   action='store_true', help='backup the scorekeeper database to cloud')
    parser.add_argument('--restore',  action='store_true', help='download the latest scorekeeper backup and restore it')
    parser.add_argument('--list',     action='store_true', help='list the files in the bucket')
    parser.add_argument('--upload',                        help='upload the given file to cloud')
    parser.add_argument('--download',                      help='download the given file from the cloud')
    parser.add_argument('--credsfile', default='creds.json',        help='if interacting with cloud storage, the creds file for connecting, defaults to creds.json')
    parser.add_argument('--bucket',    default='scorekeeperbackup', help='if interacting with cloud storage, the creds file for connecting, defaults to scorekeeperbackup')
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(-1)
    args = parser.parse_args()

    if args.local:
        zipname = dumpdb()
        print("Written to {}".format(zipname))
        sys.exit(0)

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = args.credsfile
    bucket = storage.Client().get_bucket(args.bucket)

    if args.list:
        for f in bucket.list_blobs():
            print("{} {}".format(f.time_created.strftime("%Y-%m-%d %H:%M"), f.name))

    elif args.upload:
        bucket.blob(args.upload).upload_from_filename(args.upload)

    elif args.download:
        bucket.blob(args.download).download_to_filename(args.download)

    elif args.restore:
        # Find the latest file matching our filename pattern, download it and restore
        nmatch  = re.compile("scorekeeper-\S+.sql.zip")
        zipname = max(filter(lambda x: bool(nmatch.search(x.name)), bucket.list_blobs()), key=operator.attrgetter('time_created')).name
        bucket.blob(zipname).download_to_filename(zipname)
        restoredb(zipname)
        os.remove(zipname)

    elif args.backup:
        zipname = dumpdb()
        bucket.blob(zipname).upload_from_filename(zipname)
        os.remove(zipname)

