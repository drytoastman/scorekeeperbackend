#!/usr/bin/env python3

import argparse
import datetime
import gzip
import operator
import os
import re
import subprocess
import sys

from google.cloud import storage
from google.cloud.storage import Blob

def dumpdb():
    dumpfile = datetime.date.today().strftime("scorekeeper-%Y-%m-%d.dump")
    gzipfile = dumpfile+".gz"
    subprocess.run(["pg_dumpall", "-h", "127.0.0.1", "-p", "6432", "-U", "postgres", "-f", dumpfile])
    with open(dumpfile, 'rb') as f_in, gzip.open(gzipfile, 'wb') as f_out:
        f_out.writelines(f_in)
    os.remove(dumpfile)
    return gzipfile


def restoredb(gzipfile):
    dumpfile = gzipfile[:-3]
    with gzip.open(gzipfile, 'rb') as f_in, open(dumpfile, 'wb') as f_out:
        f_out.writelines(f_in)
    subprocess.run(["psql", "-h", "127.0.0.1", "-p", "6432", "-U", "postgres", "-c", "DROP DATABASE scorekeeper;"])
    subprocess.run(["psql", "-h", "127.0.0.1", "-p", "6432", "-U", "postgres", "-f", dumpfile])
    os.remove(dumpfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Interact with Google Cloud Backup')
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
        nmatch = re.compile("scorekeeper-\S+.dump.gz")
        gzipfile = max(filter(lambda x: bool(nmatch.search(x.name)), bucket.list_blobs()), key=operator.attrgetter('time_created')).name
        bucket.blob(gzipfile).download_to_filename(gzipfile)
        restoredb(gzipfile)
        os.remove(gzipfile)

    elif args.backup:
        gzipfile = dumpdb()
        bucket.blob(gzipfile).upload_from_filename(gzipfile)
        os.remove(gzipfile)

