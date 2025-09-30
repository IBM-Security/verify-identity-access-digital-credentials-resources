#!/bin/bash

#######################################
# Delete our generated keys and certs #
#######################################

delete_certs() {
    pushd $1 
    rm -f *.pem *.key *.crt *.cert *.csr *.srl
    popd
}

delete_certs postgres_config
delete_certs oidc_provider_config
delete_certs iag_config
delete_certs config
delete_certs .