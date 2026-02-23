# Local Deployment Script

The `deploy_locally.sh` script provides a convenient way to deploy both dc-agency services and web applications locally using Docker Compose.

## Prerequisites

Before using this script, ensure you have:

1. Docker and Docker Compose installed
2. Python 3.x installed
3. Set up a Python virtual environment and installed dependencies:

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
./deploy_locally.sh [all|web-apps|dc-agency] [up|down] [options]
```

### Options

- `all`: Deploy both dc-agency services and web-apps (default)
- `web-apps`: Deploy only the web-apps (bank-app and dmv-app)
- `dc-agency`: Deploy only the dc-agency services
- `up`: Start the services (default)
- `down`: Stop the services
- `--idp-client-id VALUE`: Specify the IDP client ID
- `--idp-client-secret VALUE`: Specify the IDP client secret
- `--idp-url VALUE`: Specify the IDP URL

### Notes

- The IDP options are required for all 'up' actions
- If not provided, you will be prompted to enter them interactively

### Examples

```bash
# Deploy both dc-agency and web-apps
./deploy_locally.sh
# or
./deploy_locally.sh all up

# Deploy only web-apps
./deploy_locally.sh web-apps

# Deploy only dc-agency services
./deploy_locally.sh dc-agency

# Stop all services
./deploy_locally.sh all down

# Stop only web-apps
./deploy_locally.sh web-apps down

# Stop only dc-agency services
./deploy_locally.sh dc-agency down

# Deploy with specific IDP credentials
./deploy_locally.sh all up --idp-client-id abc123 --idp-client-secret xyz789 --idp-url https://example.com
```

## What the Script Does

When deploying services, the script:

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

## Environment Configuration

When deploying web-apps, the script configures the following environment variables:

- DMV App URL: http://localhost:8090
- Bank App URL: http://localhost:8091
- Agency URL: https://iviadcgw:8443/diagency
- OIDC Token Endpoint: https://iviadcgw:8443/oauth2/token
- IDP URL: Provided via command line or interactive prompt
- Client ID and Secret: Provided via command line or interactive prompt

These environment variables are used by:

1. The init.py script to set up agents, credential schemas, and definitions
2. The server.mjs files to generate runtime configuration (config.js) for the web applications
3. The setupProxy.mjs files to handle authentication and request forwarding to external services

The environment configuration is stored in a .env file and made available to both the server and client-side code through the config.js mechanism.

### Authentication Flow

The applications implement a secure authentication flow where:

1. The server-side proxy (setupProxy.mjs) handles token acquisition and management
2. Access tokens for the Digital Credentials agency are obtained and refreshed server-side
3. Client-side code makes requests through the proxy without directly handling tokens
4. The proxy automatically adds authentication headers to outgoing requests

## Mobile Connectivity Warning

**Important:** When running the applications locally, you may not be able to complete a full end-to-end demo with a mobile wallet app unless your mobile device:

1. Is connected to the same network as your computer running Docker
2. Can access the Docker network and resolve the container hostname `iviadcgw`
3. Can connect to the gateway via `iviadcgw:8443`

This is because the mobile wallet app needs to communicate directly with the gateway container to complete the credential issuance process. In most local setups, mobile devices cannot resolve Docker container hostnames or access the Docker network directly.

### Possible Workarounds:

- Use a mobile emulator on the same machine running Docker
- Configure network port forwarding and DNS resolution (advanced)
- For testing purposes, use the "Add to a wallet on this device" link when viewing the QR code if you're using the same device for both the web app and wallet app

## Troubleshooting

If you encounter issues:

1. Ensure Docker and Docker Compose are running
2. Check that no other services are using ports 8090 and 8091
3. Verify that Python dependencies are installed correctly
4. Check Docker logs for any error messages:
   ```bash
   docker logs iviadcgw
   docker logs bank-app
   docker logs dmv-app
5. Make sure you always run `down` and then `up` in order to get a clean instance of your services running 