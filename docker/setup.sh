#!/bin/bash

###############################
# Generate our keys and certs #
###############################

# Check if the optional gateway DNS parameter has been set and append
# it to the IAG req.conf file if so
cp ./iag_config/req.conf ./iag_config/req.conf.bak

if [[ -n $1 ]]; then
    echo -e "\nDNS.3 = $1" >> ./iag_config/req.conf
fi

# Generate CA cert
openssl req -new -x509 \
  -days 1825 \
  -config req-ca.conf \
  -keyout iviadc-ca.key \
  -out iviadc-ca.pem -nodes

# Generate service keys and certs

gen_certs() {
    pushd $1
    ./certs.sh
    popd
}

# Postgres depends on nothing
gen_certs postgres_config

# OIDC depends on Postgres
gen_certs oidc_provider_config

# IAG depends on OIDC
gen_certs iag_config

# DC depends on Postgres and IAG
gen_certs config

cp ./iag_config/req.conf.bak ./iag_config/req.conf
rm ./iag_config/req.conf.bak