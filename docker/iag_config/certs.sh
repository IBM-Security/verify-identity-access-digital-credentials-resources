#!/bin/bash

IAG_PRIVATE_KEY=iviadcgw_priv.key
IAG_PUBLIC_CERT=iviadcgw_pub.crt
IAG_PRIV_PUB=iviadcgw_priv_pub.pem

rm -f $IAG_PRIVATE_KEY
rm -f $IAG_PUBLIC_CERT
rm -f $IAG_PRIV_PUB

openssl req -x509 -newkey rsa:4096 -keyout $IAG_PRIVATE_KEY -out $IAG_PUBLIC_CERT -days 365 -config req.conf -nodes

# Not recommended for production
chmod a+r $IAG_PRIVATE_KEY

cat $IAG_PRIVATE_KEY $IAG_PUBLIC_CERT > $IAG_PRIV_PUB

echo
echo "Public key certificate: "
echo

openssl x509 -in $IAG_PRIV_PUB -text

echo
echo "Private key details: "
echo

openssl rsa -in $IAG_PRIV_PUB -text

cp -f ${IAG_PUBLIC_CERT} ../config/

IVJWT_PRIVATE_KEY=ivjwt.key
IVJWT_PUBLIC_CERT=ivjwt.crt
IVJWT_PRIV_PUB=ivjwt_priv_pub.pem

rm -f $IVJWT_PRIVATE_KEY
rm -f $IVJWT_PUBLIC_CERT
rm -f $IVJWT_PRIV_PUB

openssl req -x509 -newkey rsa:4096 -keyout $IVJWT_PRIVATE_KEY -out $IVJWT_PUBLIC_CERT -days 365 -config ivjwt_req.conf -nodes

# Not recommended for production
chmod a+r $IVJWT_PRIVATE_KEY

cat $IVJWT_PRIVATE_KEY $IVJWT_PUBLIC_CERT > $IVJWT_PRIV_PUB

echo
echo "Public key certificate: "
echo

openssl x509 -in $IVJWT_PRIV_PUB -text

echo
echo "Private key details: "
echo

openssl rsa -in $IVJWT_PRIV_PUB -text
