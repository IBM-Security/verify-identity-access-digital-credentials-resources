#!/bin/bash

# Start with iviadc.key and iviadc.crt

PRIVATE_KEY=iviadc_priv.key
PUBLIC_CERT=iviadc_pub.crt
PRIV_PUB=iviadc_priv_pub.pem
CSR=iviadc.csr
REQ_CONF=req.conf
CA_PUBLIC=../iviadc-ca.pem
CA_PRIVATE=../iviadc-ca.key

source ../run-generate-for-single-dir.sh

cp -f ${PUBLIC_CERT} ../iag_config/

openssl ecparam -name prime256v1 -genkey -noout -out oid4vci_nonce_private_key.pem