#!/bin/bash
# Makes unique files based on creation date/time
# for rotated log files with extension 1-9
# Puts them in a directory
# Log files are in current diretcory


DIRECTORY=$1
XFR_DIR=$2
ROOT_NAME=$3
S3_TARGET=$4

mkdir -p $XFR_DIR


echo "$DIRECTORY $XFR_DIR $ROOT_NAME $S3_TARGET"
for i in $DIRECTORY/*[0-9]; do
    echo xfr $i
    cp $i $XFR_DIR/${ROOT_NAME}_$(date -r $i  +%F-%T)
done


aws s3 cp --recursive $XFR_DIR/ $S3_TARGET
