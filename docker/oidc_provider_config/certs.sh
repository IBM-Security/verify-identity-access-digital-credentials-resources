#!/bin/bash

OP_PRIVATE_KEY=op_server_priv.key
OP_PUBLIC_CERT=op_server_pub.crt
DB_CERT=iviadcdb_ca.pem

rm -f $OP_PRIVATE_KEY
rm -f $OP_PUBLIC_CERT

openssl req -x509 -newkey rsa:4096 -keyout $OP_PRIVATE_KEY -out $OP_PUBLIC_CERT -days 365 -config req.conf -nodes

echo
echo "Public key certificate: "
echo

openssl x509 -in $OP_PUBLIC_CERT -text

cp -f provider.template provider.yml
for filename in ${OP_PUBLIC_CERT} ${OP_PRIVATE_KEY} ${DB_CERT}; do
    sed -I "" 's/<'${filename}'>/'$(cat ${filename} | base64)'/g' provider.yml
done

TARGET_CA=iviadcop_ca.pem
cp -f ${OP_PUBLIC_CERT} ../config/${TARGET_CA}
cp -f ${OP_PUBLIC_CERT} ../iag_config/${TARGET_CA}