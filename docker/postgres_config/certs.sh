#!/bin/bash

PG_PRIVATE_KEY=iviadcdb_priv.key
PG_PUBLIC_CERT=iviadcdb_pub.crt
PG_PRIV_PUB=iviadcdb_priv_pub.pem

rm -f $PG_PRIVATE_KEY
rm -f $PG_PUBLIC_CERT
rm -f $PG_PRIV_PUB

openssl req -x509 -newkey rsa:4096 -keyout $PG_PRIVATE_KEY -out $PG_PUBLIC_CERT -days 365 -config req.conf -nodes

# Not recommended for production
chmod a+r $PG_PRIVATE_KEY

cat $PG_PRIVATE_KEY $PG_PUBLIC_CERT > $PG_PRIV_PUB

echo
echo "Public key certificate: "
echo

openssl x509 -in $PG_PRIV_PUB -text

echo
echo "Private key details: "
echo

openssl rsa -in $PG_PRIV_PUB -text

cp -f ${PG_PUBLIC_CERT} ../config/
cp -f ${PG_PUBLIC_CERT} ../oidc_provider_config/