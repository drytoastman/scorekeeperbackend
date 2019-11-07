#!/bin/bash

if [ $# -ne 3 ] || ( [ $1 != 'backup' ] && [ $1 != 'restore' ] ); then
    echo "Usage: $0 [backup/restore] [prefix] [archive]";
    exit -1;
fi

for VOL in 'certs' 'webdata' 'emaildata' 'crondata'; do
    docker volume create $2_$VOL;
done

if [ $1 = 'backup' ]; then
    CMD="tar -czvf /host/$3 /certs /webdata /emaildata /crondata"
fi 

if [ $1 = 'restore' ]; then
    CMD="tar -C / -xvf /host/$3"
fi

docker run --rm -v ${PWD#/cygdrive}:/host \
                -v $2_certs:/certs \
                -v $2_webdata:/webdata \
                -v $2_emaildata:/emaildata \
                -v $2_crondata:/crondata \
                alpine $CMD
