#!/bin/bash

PRIVATE_KEY=iviadcop_priv.key # pragma: allowlist secret
PUBLIC_CERT=iviadcop_pub.crt
PRIV_PUB=iviadcop_priv_pub.pem
CSR=iviadcop.csr
REQ_CONF=req.conf
CA_PUBLIC=../iviadc-ca.pem
CA_PRIVATE=../iviadc-ca.key

source ../run-generate-for-single-dir.sh

cp -f ${PUBLIC_CERT} ../config/
cp -f ${PUBLIC_CERT} ../iag_config/