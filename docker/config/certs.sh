#!/bin/bash

DC_PRIVATE_KEY=dc_priv.key
DC_PUBLIC_CERT=dc_pub.crt
DC_KEYDB=dc_keydb.pem

rm -f $DC_PRIVATE_KEY
rm -f $DC_PUBLIC_CERT
rm -f $DC_KEYDB

openssl req -x509 -newkey rsa:4096 -keyout $DC_PRIVATE_KEY -out $DC_PUBLIC_CERT -days 365 -config req.conf -nodes

cat $DC_PRIVATE_KEY $DC_PUBLIC_CERT > $DC_KEYDB

echo
echo "Public key certificate: "
echo

openssl x509 -in $DC_KEYDB -text

echo
echo "Private key details: "
echo

openssl rsa -in $DC_KEYDB -text

TARGET_CA=iviadcgw_ca.pem
cp -f ${DC_PUBLIC_CERT} ../config/${TARGET_CA}