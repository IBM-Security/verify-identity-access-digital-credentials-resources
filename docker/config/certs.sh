#!/bin/bash

DC_PRIVATE_KEY=iviadc_priv.key
DC_PUBLIC_CERT=iviadc_pub.crt
DC_PRIV_PUB=iviadc_priv_pub.pem

rm -f $DC_PRIVATE_KEY
rm -f $DC_PUBLIC_CERT
rm -f $DC_PRIV_PUB

openssl req -x509 -newkey rsa:4096 -keyout $DC_PRIVATE_KEY -out $DC_PUBLIC_CERT -days 365 -config req.conf -nodes

# Not recommended for production
chmod a+r $DC_PRIVATE_KEY

cat $DC_PRIVATE_KEY $DC_PUBLIC_CERT > $DC_PRIV_PUB

echo
echo "Public key certificate: "
echo

openssl x509 -in $DC_PRIV_PUB -text

echo
echo "Private key details: "
echo

openssl rsa -in $DC_PRIV_PUB -text

cp -f ${DC_PUBLIC_CERT} ../iag_config/