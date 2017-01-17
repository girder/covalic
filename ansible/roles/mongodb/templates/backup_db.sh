#!/bin/bash
fname=mongodump_$(date +%Y%m%d_%H%M%S)
mongodump -h {{ mongo_private_ip }} -d girder -o $fname || exit 1
echo "Archiving girder_db_dump"
tar cjvf ${fname}.tar.bz2 $fname && rm -rf $fname
echo "Uploading girder_db_dump.tar.bz2 to S3 covalic-backup bucket"
python `dirname $0`/upload_to_s3.py ${fname}.tar.bz2 covalic-backup && rm ${fname}.tar.bz2
