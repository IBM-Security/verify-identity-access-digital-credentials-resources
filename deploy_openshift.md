# OpenShift Deployment Script

The `deploy_openshift.sh` script manages the deployment of both dc-agency services and web applications to an OpenShift cluster.

## Prerequisites

Before using this script, ensure you have:

1. Access to an OpenShift cluster that has egress communication enabled for port 443 to your IDP
2. OpenShift CLI (`oc`) installed and configured
3. `kubectl` installed
4. `jq` installed
5. Docker installed (for building images)
6. IBM Cloud API key (for accessing container images)
7. Python 3.x installed
8. Set up a Python virtual environment and installed dependencies:

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

## Usage

```bash
./deploy_openshift.sh [command] [options] <project-name>
```

### Commands

- `build`: Build Docker images for the web apps
- `push`: Push Docker images to the registry
- `deploy`: Deploy services to OpenShift (default)
- `undeploy`: Undeploy services from OpenShift
- `create-secret`: Create repository secret (for dc-agency services)

### Required Parameters

For build, push, deploy:
- `--registry <url>`: Container registry URL
- `--registry-namespace <ns>`: Registry namespace

For deploy (in addition to the two arguments above):
- `--idp-url <url>`: IDP URL 
- `--idp-client-id <id>`: IDP Client ID
- `--idp-client-secret <secret>`: IDP Client secret
- `--apps-domain <domain>`: Domain for app routes 

For create-secret:
- `--registry <url>`: Container registry URL
- `--docker-username <user>`: Docker registry username
- `--docker-password <pwd>`: Docker registry password/API key

### Options

- `--web-apps-only`: Deploy only the web apps
- `--dc-agency-only`: Deploy only the dc-agency services

### Examples

```bash
# Build web app images
./deploy_openshift.sh build --registry icr.io --registry-namespace myorg/myrepo my-project

# Push web app images to registry
./deploy_openshift.sh push --registry icr.io --registry-namespace myorg/myrepo my-project

# Create repository secret
./deploy_openshift.sh create-secret --registry icr.io --docker-username iamapikey --docker-password <apikey>

# Deploy both dc-agency and web-apps (default)
./deploy_openshift.sh deploy --registry icr.io --registry-namespace myorg/myrepo --apps-domain example.com --idp-url https://example.com --idp-client-id abc123 --idp-client-secret xyz789 my-project

# Deploy only web-apps
./deploy_openshift.sh deploy --registry icr.io --registry-namespace myorg/myrepo --web-apps-only --apps-domain example.com --idp-url https://example.com --idp-client-id abc123 --idp-client-secret xyz789 my-project

# Deploy only dc-agency services
./deploy_openshift.sh deploy --registry icr.io --registry-namespace myorg/myrepo --dc-agency-only --apps-domain example.com --idp-client-id abc123 --idp-client-secret xyz789 my-project

# Undeploy services
./deploy_openshift.sh undeploy my-project                # Undeploy both
./deploy_openshift.sh undeploy --web-apps-only my-project # Undeploy only web-apps
./deploy_openshift.sh undeploy --dc-agency-only my-project # Undeploy only dc-agency services
```

## What the Script Does

### Building and Pushing Images

The script can build Docker images for the web applications and push them to a container registry:

1. `build`: Builds the bank-app and dmv-app Docker images with the specified registry and namespace, and optional project name suffix
2. `push`: Pushes the images to the specified registry and namespace

### Deployment Process

When deploying services, the script:

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

### Environment Configuration

The script configures the environment by:
- Determining hostnames from routes
- Setting up agency URL and token endpoint
- Running init.py with the provided parameters
- Creating a ConfigMap from the generated .env file

The environment configuration is used by:

1. The init.py script to set up agents, credential schemas, and definitions
2. The server.mjs files to generate runtime configuration (config.js) for the web applications
3. The setupProxy.mjs files to handle authentication and request forwarding to external services

When deployed to OpenShift, the applications use the same runtime configuration mechanism as the local deployment, but with the ConfigMap providing the environment variables instead of a .env file. This allows for consistent behavior across deployment environments.

### Authentication Architecture

The OpenShift deployment maintains the same secure authentication architecture as the local deployment:

1. The server-side proxy (setupProxy.mjs) handles token acquisition and management
2. Access tokens for the Digital Credentials agency are obtained and refreshed server-side
3. Client-side code makes requests through the proxy without directly handling tokens
4. The proxy automatically adds authentication headers to outgoing requests

This architecture ensures that sensitive credentials and tokens are never exposed to the client-side code, enhancing the security of the applications.

## Project Management

If a project name is provided:
- For new deployments, the script creates a new project
- For existing projects, the script switches to that project
- After operations are complete, the script switches back to the original project

## Troubleshooting

If you encounter issues:

1. Ensure you're logged in to your OpenShift cluster
2. Verify that the required secrets exist
3. Check that the provided IDP URL, client ID, and client secret are correct
4. Examine the OpenShift logs for any error messages
5. Verify that Python dependencies are installed correctly
6. Make sure you always `undeploy` and then `deploy` in order to get a clean instance of your services running 
