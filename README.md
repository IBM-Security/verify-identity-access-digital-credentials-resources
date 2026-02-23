# IBM Verify Identity Access Digital Credentials

This repository contains sample applications demonstrating the implementation of OpenID for Verifiable Credentials (OID4VC) using IBM Verify Identity Access Digital Credentials.

## Overview

The repository includes three main components:

1. **dc-agency** - Backend services for Digital Credentials issuance and verification
2. **dmv-app** - A sample DMV (Department of Motor Vehicles) application that issues digital credentials
3. **bank-app** - A sample banking application that verifies digital credentials

These applications demonstrate the end-to-end flow of issuing and verifying digital credentials using the OID4VC protocol.

## Prerequisites

Before you begin, ensure you have the following installed:

- Docker and Docker Compose
- Python 3.x
- Node.js and npm
- `oc` (OpenShift CLI)
- `kubectl`
- `jq`

For OpenShift deployment, you'll also need:

- Access to an OpenShift cluster that has egress communication enabled for port 443 to your IDP
- IBM Cloud API key (for accessing container images)
- IVIADC license key (obtainable from [IBM Verify trial page](https://isva-trial.verify.ibm.com/), clicking the `Digital Credentials Code` download button)

The IDP configured for the DMV application is currently https://demos.verify.ibm.com/ - you will need to request access to this tenant by completing this form or contacting Robert Graham: [Verify Demos Tenant Sign Up Form](https://demos.verify.ibm.com/flows/?reference=ibmer_registration_flow).

If you cannot get access to this tenant, you can set up your own IDP. Create an OIDC application with the following parameters:
- Application URL: URL of the deployed DMV application
- Grant types: Authorization code
- Redirect URLS: https://<deployed-gateway-host>/pkmsoidc and https://<deployed-dmv-host>/logincallback
Take note of the client ID and client secret, you'll need these in the deployment step.

## Python Environment Setup

Before running any deployment scripts, you need to set up a Python virtual environment and install the required dependencies:

```bash
# Create a Python virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

## Setup Instructions
 
### 1. Clone the Repository

```bash
git clone https://github.ibm.com/IVIDC/oid4vc-sample-apps.git
cd oid4vc-sample-apps
```

### 2. One-time creation of config.yaml

1. Create an instance of config.yaml with your license key:
    ```bash
    cp dc-agency/docker/config/config.template dc-agency/docker/config/config.yaml
    sed -i.bak 's#LICENSE_PLACEHOLDER#<insert-license-key-string-here>#' config/config.yaml
    rm -f config/config.yaml.bak
    ```

### 3. Deployment Options

You can deploy the applications using either Docker Compose (locally) or OpenShift.

## Local Deployment with Docker Compose

The `deploy_locally.sh` script provides a convenient way to deploy both dc-agency services and web applications locally using Docker Compose.

### Prerequisites for Local Deployment

1. Docker and Docker Compose installed
2. Python 3.x installed
3. Python virtual environment set up and dependencies installed (see Python Environment Setup section)

### Local Deployment Commands

```bash
# Deploy both dc-agency services and web-apps (default)
./deploy_locally.sh
# or
./deploy_locally.sh all up

# Deploy only dc-agency services
./deploy_locally.sh dc-agency

# Deploy only web-apps (bank-app and dmv-app)
./deploy_locally.sh web-apps

# Stop all services
./deploy_locally.sh all down

# Stop only dc-agency services
./deploy_locally.sh dc-agency down

# Stop only web-apps
./deploy_locally.sh web-apps down
```

### What Happens During Local Deployment

When deploying services locally, the script:

1. For dc-agency services:
   - Runs setup.sh to generate certificates
   - Uses the Docker Compose file in the dc-agency/docker directory
   - Waits for essential services (iviadcgw, iviadcop, iviadc) to be ready

2. For web-apps:
   - Installs required Python dependencies
   - Initializes the environment by running init.py with proper parameters
   - Creates a .env file with configuration for the web applications
   - Starts the web-apps using docker-compose-webapps.yml
   - Waits for the web applications to be ready

### Mobile Connectivity Limitation

**Important:** When running the applications locally, you may not be able to complete a full end-to-end demo with a mobile wallet app. This is because the mobile device needs to:

1. Be connected to the same network as your computer running Docker
2. Be able to access the Docker network and resolve the container hostname `iviadcgw`
3. Connect to the gateway via `iviadcgw:8443`

In most local setups, mobile devices cannot resolve Docker container hostnames or access the Docker network directly, which prevents the credential issuance process from completing successfully on a mobile wallet.

For more details and possible workarounds, see the [Local Deployment documentation](deploy_locally.md#mobile-connectivity-warning).

## OpenShift Deployment

The `deploy_openshift.sh` script manages the deployment of both dc-agency services and web applications to an OpenShift cluster.

### Prerequisites for OpenShift Deployment

1. Access to an OpenShift cluster
2. OpenShift CLI (`oc`) installed and configured
3. `kubectl` installed
4. `jq` installed
5. Docker installed (for building images)
6. IBM Cloud API key (for accessing container images)
7. IVIADC license key
8. Python virtual environment set up and dependencies installed (see Python Environment Setup section)

### Log in to the Docker registry and the OpenShift cluster

Log in to your OpenShift cluster:
```(Copy login command from OpenShift web console)```

Log in to your docker registry:
```docker login -u <user> -p <password> <registry>```
If using icr.io in IBM Cloud as your container registry:
```docker login -u iamapikey -p <yourIBMCloudAPIkey> icr.io```

### OpenShift Deployment Commands

```bash
# Create a secret for accessing container images
./deploy_openshift.sh create-secret --registry <registry> --docker-username <user> --docker-password <password>
# OR if using icr.io in IBM Cloud as your container registry
./deploy_openshift.sh create-secret --registry icr.io --docker-username iamapikey --docker-password <yourIBMCloudAPIkey>

# Build Docker images for the web apps (optionally with openshift project name suffix)
./deploy_openshift.sh build --registry icr.io --registry-namespace myorg/myrepo [openshift-project-name]

# Push images to container registry
./deploy_openshift.sh push --registry icr.io --registry-namespace myorg/myrepo [openshift-project-name]

# Deploy both dc-agency services and web applications
./deploy_openshift.sh deploy --registry icr.io --registry-namespace myorg/myrepo --idp-url <idp_url> --idp-client-id <client_id> --idp-client-secret <client_secret> [--apps-domain <domain>] [openshift-project-name]

# OR Deploy DC agency services only
./deploy_openshift.sh deploy --registry icr.io --registry-namespace myorg/myrepo --dc-agency-only --idp-client-id <client_id> --idp-client-secret <client_secret> [--apps-domain <domain>] [openshift-project-name]

# OR Deploy web applications only
./deploy_openshift.sh deploy --registry icr.io --registry-namespace myorg/myrepo --web-apps-only --idp-url <idp_url> --idp-client-id <client_id> --idp-client-secret <client_secret> [--apps-domain <domain>] [openshift-project-name]
```

### Example OpenShift Deployment Command

```bash
# Deploy both dc-agency and web-apps to a project named "oid4vc-demo"
./deploy_openshift.sh deploy --registry icr.io --registry-namespace myorg/myrepo --idp-url https://example.idp.com --idp-client-id abc123 --idp-client-secret xyz789 --apps-domain example.com oid4vc-demo
```

### What Happens During OpenShift Deployment

When deploying services to OpenShift, the script:

1. For dc-agency services:
   - Creates a new project if specified
   - Creates service accounts and grants necessary permissions
   - Configures routes and hostnames
   - Generates service certificates
   - Creates ConfigMaps for various components
   - Deploys the pods
   - Waits for essential services to be ready

2. For web-apps:
   - Applies network policies
   - Configures routes
   - Runs init.py to initialize the environment
   - Creates ConfigMap from the .env file
   - Deploys the applications

### Project Management in OpenShift

If a project name is provided:
- For new deployments, the script creates a new project
- For existing projects, the script switches to that project
- After operations are complete, the script switches back to the original project

### OpenShift Deployment URLs

The URLs for accessing the Bank and DMV apps are printed in the output of the `deploy` command.


## Cleanup

### Local Deployment Cleanup

```bash
# Stop all services
./deploy_locally.sh all down

# Stop only dc-agency services
./deploy_locally.sh dc-agency down

# Stop only web-apps
./deploy_locally.sh web-apps down
```

### OpenShift Deployment Cleanup

```bash
# Undeploy web applications
./deploy_openshift.sh undeploy --web-apps-only [openshift-project-name]

# Undeploy DC agency services
./deploy_openshift.sh undeploy --dc-agency-only [openshift-project-name]

# Undeploy both
./deploy_openshift.sh undeploy [openshift-project-name]
```

## Usage

Once deployed, you can access the apps at the hostnames you've configured in your routes.yaml file, or by looking up the automatically generated hostnames from the OpenShift console. The URLs are also printed in the output of the `deploy` command.

### Sample Workflow

1. Access the DMV application and log in
2. Create a digital driver's license
3. Access the Bank application
4. Use the digital credential to verify your identity

## Troubleshooting

### Local Deployment Issues

If you encounter issues with local deployment:

1. Ensure Docker and Docker Compose are running
2. Check that no other services are using ports 8090 and 8091
3. Verify that Python dependencies are installed correctly
4. Check Docker logs for any error messages:
   ```bash
   docker logs iviadc
   docker logs bank-app
   docker logs dmv-app
   ```
5. Make sure you always run `down` and then `up` in order to get a clean instance of your services running

### OpenShift Deployment Issues

If you encounter issues with OpenShift deployment:

1. Ensure you're logged in to your OpenShift cluster
2. Verify that the required secrets exist
3. Check that the provided IDP URL, client ID, and client secret are correct
4. Examine the OpenShift logs for any error messages
5. Verify that Python dependencies are installed correctly
6. Make sure you always run `undeploy` and then `deploy` in order to get a clean instance of your services running

### DC Agency Service Debugging

To debug the DC agency services, you can enable more detailed logging:
- For the DC service, set config/config.yaml "log_level" to "debug" 
- For the IAG service, add the following to iag_config/config.yaml:
```
logging:
  tracing:
    - file_name: /var/tmp/pdweb_snoop.log
      component: pdweb.snoop
      level: 9
```

## Runtime Environment Configuration

Both the bank-app and dmv-app use a runtime environment configuration system that:

1. Generates a `config.js` file at startup with environment variables
2. Makes these variables available to the frontend application via `window.ENV`
3. Allows for configuration changes without rebuilding the application

The server.mjs files in both applications handle this configuration generation during startup.

## Authentication and Proxy Configuration

The applications use an advanced proxy configuration to handle authentication and communication with external services:

### Server-Side Authentication

1. Access tokens for the Digital Credentials agency are obtained and managed server-side
2. The server maintains token storage and handles automatic token refresh
3. All authenticated requests to the agency are proxied through the application server
4. The server adds the appropriate authentication headers to outgoing requests

### Client-Side Implementation

1. The client-side code uses the `DiagencyApiService` to make requests
2. The service provides methods like `authenticatedRequest` and `authenticatedRawRequest`
3. These methods send requests to the proxy endpoints without handling tokens directly
4. Binary data (like QR code images) is properly handled with specialized methods

## Additional Information

- Helper scripts are available in the repository root for common tasks
- For more detailed information about specific components, refer to their respective README files