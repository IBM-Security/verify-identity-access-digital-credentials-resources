#!/bin/sh

#
# This script will allow TLS access to the vc database.
#

hbaConf=$PGDATA/pg_hba.conf

echo "hostssl vc $POSTGRES_USER all md5" >> $hbaConf
echo "hostssl postgres $POSTGRES_USER all md5" >> $hbaConf

