#!/bin/bash

OP_PRIVATE_KEY=iviadcop_priv.key
OP_PUBLIC_CERT=iviadcop_pub.crt
OP_PRIV_PUBLIC=iviadcop_priv_pub.pem
DB_CERT=iviadcdb_pub.crt

rm -f $OP_PRIVATE_KEY
rm -f $OP_PUBLIC_CERT
rm -f $OP_PRIV_PUBLIC

openssl req -x509 -newkey rsa:4096 -keyout $OP_PRIVATE_KEY -out $OP_PUBLIC_CERT -days 365 -config req.conf -nodes

# Not recommended for production
chmod a+r $OP_PRIVATE_KEY

cat $OP_PRIVATE_KEY $OP_PUBLIC_CERT > $OP_PRIV_PUBLIC

echo
echo "Public key certificate: "
echo

openssl x509 -in $OP_PRIV_PUBLIC -text

echo
echo "Private key details: "
echo

openssl rsa -in $OP_PRIV_PUBLIC -text

cp -f ${OP_PUBLIC_CERT} ../config/
cp -f ${OP_PUBLIC_CERT} ../iag_config/