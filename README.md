# IBM Verify Identity Access Digital Credentials

## Prerequisites

1. An IVIADC license key. You may obtain a trial key from [here](https://isva-trial.verify.ibm.com/).

2. `docker` / `docker-compose` or equivalents

3. Access to the following docker containers:

    *  bitnami/openldap:latest
    *  icr.io/ivia/ivia-digital-credentials:25.03
    *  icr.io/ivia/ivia-postgresql:11.0.0.0
    *  icr.io/ivia/ivia-oidc-provider:25.03
    *  icr.io/ibmappgateway/ibm-application-gateway:25.03


## One-time setup

1. Create a new docker network for this environment. The IP range can be any private IP address space that doesn't conflict with your own private address usage.

    ```bash
    docker network create --subnet 172.16.0.0/24 iviadc-default
    ```

2. Generate required keys and certificates:

    ```bash
    cd docker/
    ./setup.sh
    ```

3. Create an instance of config.yaml with your license key:
    ```bash
    cp config/config.template config/config.yaml
    sed -i "" 's/LICENSE_PLACEHOLDER/<insert-license-key-string-here>/' config/config.yaml
    ```

4. Create aliases for the various services in your hosts file:
    ```bash
    echo "127.0.0.1	iviadc iviadcdb iviadcop iviadcgw iviadcldap" >> /etc/hosts
    ```

## Runtime

1. Once your environment has been setup, you can bring the relevant containers online with:

    ```bash
    docker-compose up
    ```

## Demonstrations

1. Once the containers are running, you can execute an example scenario which will create agents and perform credential issuance/verification via the following python script (use the `-h` flag to view scenario configuration options):

    ```bash
    cd ../demonstration
    pip3 install -r ./requirements.txt
    python3 run_demonstration.py mdoc_mdl
    ```
