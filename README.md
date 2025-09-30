# IBM Verify Identity Access Digital Credentials

This version of the DC setup scripts deploys the DC containers in your local docker environment.

## Prerequisites

1. An IVIADC license key. You may obtain a trial key from [here](https://isva-trial.verify.ibm.com/), clicking the `Digital Credentials Code` download button.

2. `docker` / `docker-compose` or equivalents

3. Access to the following docker container images:

    *  bitnami/openldap:latest
    *  icr.io/ivia/ivia-digital-credentials:25.09
    *  icr.io/ivia/ivia-postgresql:11.0.1.0
    *  icr.io/ivia/ivia-oidc-provider:25.06
    *  icr.io/ibmappgateway/ibm-application-gateway:25.09

4. A MacOS or Linux system to run these scripts from. Tested MacOS Sequoia and Red Hat Enterprise Linux (RHEL) 9.5. Other environments may still work, but might require customisations.


### One-time setup

1. Create a new docker network for this environment. The IP range can be any private IP address space that doesn't conflict with your own private address usage.

    ```bash
    docker network create --subnet 172.16.0.0/24 iviadc-default
    ```

2. Generate required keys and certificates:

    ```bash
    cd docker/
    ./setup.sh
    ```

3. Create an instance of config.yaml with your license key (retrieved from Step 1 of the pre-requisites):
    ```bash
    cp config/config.template config/config.yaml
    sed -i.bak 's#LICENSE_PLACEHOLDER#<insert-license-key-string-here>#' config/config.yaml
    rm -f config/config.yaml.bak
    ```

4. Create aliases for the various services in your hosts file:
    ```bash
    echo "127.0.0.1 iviadc iviadcdb iviadcop iviadcgw iviadcldap" >> /etc/hosts
    ```

## Runtime - locally using docker-compose

1. Once your environment has been setup, you can bring the relevant containers online with:

    ```bash
    docker-compose up
    ```

2. Clean up using:

    ```bash
    docker-compose down -v
    ```

You can view the swagger docs here: https://localhost:9720/ibm/api/explorer/

## Demonstrations

### Using the demonstration utility in this repo: 

1. Once the containers are running, you can execute an example scenario which will create agents and perform credential issuance/verification via the following python script (use the `-h` flag to view scenario configuration options):

    ```bash
    cd ../demonstration
    pip3 install -r ./requirements.txt
    python3 run_demonstration.py mdoc_mdl
    ```

On success, you will see output similar to the following:
```
Demonstration summary (mdoc_mdl):
===================================
Agent client secrets are available at ./build/agents_and_client_secrets.txt
Used credential schema with id a18614b8-2043-4906-8393-f1c846614b8f
Used credential definition with id 2:mso_mdoc:840ac81f-ab75-42be-8e6b-89233215cc24
Performed credential issuance:
         |_ Issuer agent with id b6fa3069-237e-4a90-ac9f-190d9318ed7e offered a credential to holder agent id cn=user_1,ou=users,dc=ibm,dc=com
         |_ The holder accepted the offer and was issued a credential with id 73c43d8f-18d9-4798-bb16-9fe18390c02b
Performed credential verification:
         |_ Verifier agent with id e526816c-fc57-4c35-be9f-8f1612299fbd requested a proof from holder agent id cn=user_1,ou=users,dc=ibm,dc=com
         |_ The holder generated and presented a valid proof. The associated verification's id was 22b3a866-6081-4913-ae53-19d3c520e13b
```