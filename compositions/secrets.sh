#!/bin/bash

if [ $# -ne 3 ] || ( [ $1 != 'backup' ] && [ $1 != 'restore' ] ); then
    echo "Usage: $0 [backup/restore] [prefix] [archive]";
    exit -1;
fi

for VOL in 'webdata' 'emaildata' 'crondata'; do
    docker volume create $2_$VOL
done
docker volume create certs


docker run --rm --name volload -d \
           -v certs:/certs \
           -v $2_webdata:/webdata \
           -v $2_emaildata:/emaildata \
           -v $2_crondata:/crondata \
           alpine ash -c 'while sleep 3600; do :; done'

if [ $1 = 'restore' ]; then
    docker cp $3 volload:/tmp
    docker exec volload tar -C / -xvf /tmp/$3
fi

if [ $1 = 'backup' ]; then
    docker exec volload tar -czvf /tmp/backup.tgz /certs /webdata /emaildata /crondata
    docker cp volload:/tmp/backup.tgz $3
fi

docker kill volload
