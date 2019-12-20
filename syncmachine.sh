#!/bin/bash
MACHINE=$1
SYNCDIR=$2
SYNCDIR="${SYNCDIR:=${PWD}}/"
MACHINE_DIR="${MACHINE}:${SYNCDIR}/"
TEMPDIR=$(mktemp -d)

function cleanup(){
    rm -r ${TEMPDIR}
    kill -SIGTERM $$
}

function main() {
    docker-machine ssh ${MACHINE} "mkdir -p ${SYNCDIR}"
    docker-machine mount ${MACHINE_DIR} ${TEMPDIR}    
    rsync -r --info=progress2 ${SYNCDIR} ${TEMPDIR}
    echo "initial sync finished"
    inotifywait -r -m -e close_write --format '%w%f' ${SYNCDIR} | while read CHANGED_FILE
    do
        rsync ${CHANGED_FILE} ${TEMPDIR}
    	echo "file ${CHANGED_FILE} synced"
    done
}

trap cleanup INT
main
