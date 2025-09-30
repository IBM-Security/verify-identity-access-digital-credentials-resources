#!/bin/bash

# Start with iviadcgw.key and iviadcgw.crt

PRIVATE_KEY=iviadcgw_priv.key # pragma: allowlist secret
PUBLIC_CERT=iviadcgw_pub.crt
PRIV_PUB=iviadcgw_priv_pub.pem
CSR=iviadcgw.csr
REQ_CONF=req.conf
CA_PUBLIC=../iviadc-ca.pem
CA_PRIVATE=../iviadc-ca.key

source ../run-generate-for-single-dir.sh

cp -f ${PUBLIC_CERT} ../config/

## Then ivjwt.key and ivjwt.crt

PRIVATE_KEY=ivjwt.key # pragma: allowlist secret
PUBLIC_CERT=ivjwt.crt
PRIV_PUB=ivjwt_priv_pub.pem
CSR=ivjwt.csr
REQ_CONF=ivjwt_req.conf
CA_PUBLIC=../iviadc-ca.pem
CA_PRIVATE=../iviadc-ca.key

source ../run-generate-for-single-dir.sh
