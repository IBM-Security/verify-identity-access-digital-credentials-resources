#!/bin/bash

PRIVATE_KEY=iviadcdb_priv.key # pragma: allowlist secret
PUBLIC_CERT=iviadcdb_pub.crt
PRIV_PUB=iviadcdb_priv_pub.pem
CSR=iviadcdb.csr
REQ_CONF=req.conf
CA_PUBLIC=../iviadc-ca.pem
CA_PRIVATE=../iviadc-ca.key

source ../run-generate-for-single-dir.sh

cp -f ${PUBLIC_CERT} ../config/
cp -f ${PUBLIC_CERT} ../oidc_provider_config/
