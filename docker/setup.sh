#!/bin/bash

###############################
# Generate our keys and certs #
###############################

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