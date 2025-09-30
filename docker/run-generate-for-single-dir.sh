#!/bin/bash

## This script is only intended to be run as part of the 'setup.sh'
## functionality. If you want to use this as a standalone script, refer to the 
## 'certs.sh' scripts in each service directory to set the correct environment
## variables and run this script from the context of that directory. 

rm -f $PRIVATE_KEY $PUBLIC_CERT $PRIV_PUB $CSR

# Generate service key and CSR
openssl req -new -nodes -keyout $PRIVATE_KEY -out $CSR -config $REQ_CONF

# Sign it with the CA
openssl x509 -req -in $CSR -CA $CA_PUBLIC -CAkey $CA_PRIVATE \
  -CAcreateserial -out $PUBLIC_CERT -days 365 -extensions v3_req \
  -extfile $REQ_CONF

if [ ! -z "$PRIV_PUB" ]; then
  cat $PRIVATE_KEY $PUBLIC_CERT > $PRIV_PUB
fi 

echo
echo "Public key certificate: "
echo

openssl x509 -in $PUBLIC_CERT -text

echo
echo "Private key details: "
echo

openssl rsa -in $PRIVATE_KEY -text