#!/usr/bin/env python3

"""
This script is used to create the .env file for an onpremise verifiable
credentials environment.
"""

import os
import sys
from typing import Any
import requests
import base64

def get_verify_option():
    """
    Returns the appropriate verify option for requests.
    - If CUSTOM_CA_PATH is set, use that CA bundle (for localhost with self-signed certs)
    - Otherwise, use True (system CA bundle for production)
    - NEVER returns False - certificate validation is always enabled
    
    Returns:
        str or bool: Path to custom CA bundle, or True for system CA bundle
    """
    custom_ca = os.environ.get('CUSTOM_CA_PATH')
    if custom_ca and os.path.exists(custom_ca):
        print(f"Using custom CA certificate from: {custom_ca}")
        return custom_ca
    # Always validate certificates using system CA bundle
    return True

def encode_image_file(file_path):
    """
    Read an image file and encode it as base64.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Base64 encoded image with data URI prefix
    """
    try:
        with open(file_path, 'rb') as image_file:
            image_data = image_file.read()
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            
            # Determine MIME type based on file extension
            if file_path.lower().endswith('.png'):
                mime_type = 'image/png'
            elif file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                mime_type = 'image/jpeg'
            else:
                # Default to PNG if unknown
                mime_type = 'image/png'
            
            return f"data:{mime_type};base64,{encoded_image}"
    except Exception as e:
        print(f"Error encoding image from {file_path}: {str(e)}")
        return None

# Constants
DMV_AGENT_NAME = "DMVIssuer"
BANK_AGENT_NAME = "BankVerifier"

INSTRUCTIONS = """This script is used to create the .env file for the
demo environment when the verifiable credentials environment is running
in an onpremise environment.

There are a couple of environment variables which will need to be
customised for the envionment in use, mostly AGENCY_URL and OIDC_TOKEN_ENDPOINT.

If the verifiable credentials environment is running in an OpenShift cluster
the KUBERNETES=1 environment variable can be set to tell this script to
dynamically obtain the required information.
"""

def usage():
    """Display usage instructions and exit."""
    print("Instructions:")
    print("=============")
    print(INSTRUCTIONS)
    sys.exit(1)

def get_access_token(token_endpoint, client_id, client_secret):
    """
    Retrieve an access token.
    
    Args:
        token_endpoint: OAuth token endpoint URL
        client_id: OAuth client ID
        client_secret: OAuth client secret
        
    Returns:
        Access token string
    """
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.post(token_endpoint, headers=headers, data=data, verify=get_verify_option())
    
    if response.status_code != 200:
        print(f"Error getting access token: {response.text}")
        return None
        
    return response.json().get('access_token')

def create_agent(agency_url, access_token, agent_id, agent_name, is_did_on_ledger, agent_type):
    """
    Create an agent.
    
    Args:
        agency_url: Agency URL
        access_token: Access token for authentication
        agent_id: Agent ID (can be empty string for new agents)
        agent_name: Agent name
        is_did_on_ledger: Boolean indicating if DID is on ledger
        agent_type: Type of agent (issuer or verifier)
        
    Returns:
        Agent data as dictionary
    """
    print(f"Creating the agent: {agent_name}")
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    # Check if agent already exists
    response = requests.get(f"{agency_url}/v1.0/diagency/agents", headers=headers, verify=get_verify_option())
    
    if response.status_code != 200:
        print(f"Error getting agents: {response.text}")
        return None
        
    agents = response.json()
    identifier = None
    
    for item in agents.get('items', []):
        if item.get('name') == agent_name:
            identifier = item.get('id')
            break
    
    if identifier:
        # Agent exists, get its details
        response = requests.get(
            f"{agency_url}/v1.0/diagency/agents/{identifier}?includepass=true",
            headers=headers,
            verify=get_verify_option()
        )
        
        if response.status_code != 200:
            print(f"Error getting agent details: {response.text}")
            return None
            
        return response.json()
    else:
        # Create new agent
        headers['Content-Type'] = 'application/json'
        
        agent_data = {
            'id': agent_id,
            'name': agent_name,
            'is_did_on_ledger': is_did_on_ledger,
            'agent_type': agent_type,
            'did_method': 'did:web'
        }
        
        if agent_type == "verifier":
            # For verifier, add profile with logo and 'verifier' attribute
            bank_host = os.environ.get('BANK_HOST', '')
            image_url = f"{bank_host}/logo.png"
            
            # Check if URL is HTTP and encode image if needed (API doesn't accept URI's starting with http, only data: and https:)
            logo_data = {}
            if bank_host and bank_host.startswith('http://'):
                print(f"Bank host uses HTTP, encoding logo image from file...")
                # Use the local file path instead of URL
                logo_file_path = "bank-app/public/logo.png"
                encoded_image = encode_image_file(logo_file_path)
                if encoded_image:
                    logo_data = {'uri': encoded_image}
                else:
                    # Fallback to URL if encoding fails
                    logo_data = {'uri': image_url}
            else:
                logo_data = {'uri': image_url}
            
            agent_data['profile'] = {
                'verifier': {
                    'root_of_trust': {
                        'system_generated': {}
                    },
                    'metadata': {
                        'response_types': ['vp_token'],
                        'vp_formats_supported': {
                            'mso_mdoc': {
                                'issuerauth_alg_values': [-9, -7],
                                'deviceauth_alg_values': [-9, -7]
                            }
                        }
                    },
                    'default_exchange_template': {
                        'response_mode': 'direct_post',
                        'client_id_prefix': 'redirect_uri',
                        'request_mode': 'by_value_params',
                        'default_authorization_url_scheme': 'openid4vp://',
                        'ttl': 120
                    }
                },
                'display': [
                    {
                        'locale': 'en-AU',
                        'name': 'Smart Money Bank',
                        'logo': logo_data
                    }
                ]
            }
        
        elif agent_type == "issuer":
            # For issuer, add profile with logo
            dmv_host = os.environ.get('DMV_HOST', '')
            image_url = f"{dmv_host}/logo.png"
            
            # Check if URL is HTTP and encode image if needed (API doesn't accept URI's starting with http, only data: and https:)
            logo_data = {}
            if dmv_host and dmv_host.startswith('http://'):
                print(f"DMV host uses HTTP, encoding logo image from file...")
                # Use the local file path instead of URL
                logo_file_path = "dmv-app/public/logo.png"
                encoded_image = encode_image_file(logo_file_path)
                if encoded_image:
                    logo_data = {'uri': encoded_image}
                else:
                    # Fallback to URL if encoding fails
                    logo_data = {'uri': image_url}
            else:
                logo_data = {'uri': image_url}

            agent_data['profile'] = {
                'display': [
                    {
                        'locale': 'en-AU',
                        'name': 'Department of Motor Vehicles',
                        'logo': logo_data
                    }
                ]
            }
        
        response = requests.post(
            f"{agency_url}/v1.0/diagency/agents?includepass=true",
            headers=headers,
            json=agent_data,
            verify=get_verify_option()
        )
        
        if response.status_code not in [200, 201]:
            print(f"Error creating agent: {response.text}")
            return None
            
        return response.json()

def create_oid4vci_credential_schema(agency_url, access_token):
    """
    Create credential schema.
    
    Args:
        agency_url: Agency URL
        access_token: Access token for authentication
        
    Returns:
        Schema ID
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    schema_data = {
        "name": "oidschema",
        "version": "1.0",
        "schema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$linkedData": {
                "identifier": "org.iso.18013.5.1.mDL",
                "@id": "https://iso.org/schemas/mdl",
                "@vocab": "https://iso.org/schemas/mdl",
                "@type": "org.iso.18013.5.1.mDL"
            },
            "$oid4vc": {
                "display": [
                    {
                        "name": "Mobile Drivers Licence",
                        "locale": "en"
                    }
                ]
            },
            "type": "object",
            "properties": {
                "org.iso.18013.5.1": {
                    "$linkedData": {
                        "identifier": "org.iso.18013.5.1",
                        "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1"
                    },
                    "type": "object",
                    "properties": {
                        "@context": {
                            "type": "array"
                        },
                        "document_number": {
                            "$linkedData": {
                                "identifier": "document_number",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/document_number"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Document number",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        },
                        "issue_date": {
                            "$linkedData": {
                                "identifier": "issue_date",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/issue_date"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Issue date",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        },
                        "expiry_date": {
                            "$linkedData": {
                                "identifier": "expiry_date",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/expiry_date"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Expiry date",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        },
                        "given_name": {
                            "$linkedData": {
                                "identifier": "given_name",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/given_name"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Given name(s)",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        },
                        "family_name": {
                            "$linkedData": {
                                "identifier": "family_name",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/family_name"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Family name",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        },
                        "birth_date": {
                            "$linkedData": {
                                "identifier": "birth_date",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/birth_date"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Date of birth",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string",
                            "format": "date"
                        },
                        "issuing_authority": {
                            "$linkedData": {
                                "identifier": "issuing_authority",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/issuing_authority"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Issuing authority",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        },
                        "resident_address": {
                            "$linkedData": {
                                "identifier": "resident_address",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/resident_address"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Permanent place of residence",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        },
                        "resident_city": {
                            "$linkedData": {
                                "identifier": "resident_city",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/resident_city"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Resident city",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        },
                        "resident_state": {
                            "$linkedData": {
                                "identifier": "resident_state",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/resident_state"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Resident state / province / district",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        },
                        "resident_postal_code": {
                            "$linkedData": {
                                "identifier": "resident_postal_code",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/resident_postal_code"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Resident postal code",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        },
                        "resident_country": {
                            "$linkedData": {
                                "identifier": "resident_country",
                                "@id": "https://iso.org/schemas/mdl/org.iso.18013.5.1/resident_country"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Resident country",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        },
                        "portrait": {
                            "$linkedData": {
                                "identifier": "portrait",
                                "@id":"https://iso.org/schemas/mdl/org.iso.18013.5.1/portrait"
                            },
                            "$oid4vc": {
                                "display": [
                                    {
                                        "name": "Portrait of holder",
                                        "locale": "en"
                                    }
                                ]
                            },
                            "type": "string"
                        }
                    },
                    "required": ["document_number", "issue_date", "expiry_date", "family_name", "given_name", "birth_date", "issuing_authority"],
                    "additionalProperties": False
                }
            },
            "required": ["org.iso.18013.5.1"],
            "additionalProperties": False
        }
    }
    
    response = requests.post(
        f"{agency_url}/v2.0/diagency/credential_schemas",
        headers=headers,
        json=schema_data,
        verify=get_verify_option()
    )
    
    if response.status_code not in [200, 201]:
        print(f"Error creating credential schema: {response.text}")
        return None
        
    return response.json().get('id')

def create_oid4vci_credential_definition(agency_url, access_token, schema_id):
    """
    Create credential definition.
    
    Args:
        agency_url: Agency URL
        access_token: Access token for authentication
        schema_id: Schema ID to use for the credential definition
        
    Returns:
        Credential definition ID
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    definition_data = {
        "schema_id": schema_id,
        "credential_document_type": ["org.iso.18013.5.1.mDL"],
        "credential_format": "mso_mdoc",
        "credential_signing_algorithm": "ESP256",
        "cryptographic_binding_methods": ["cose_key"],
        "key_proof_types": {
            "jwt": ["ES256"]
        }
    }
    
    response = requests.post(
        f"{agency_url}/v2.0/diagency/credential_definitions",
        headers=headers,
        json=definition_data,
        verify=get_verify_option()
    )
    
    if response.status_code not in [200, 201]:
        print(f"Error creating credential definition: {response.text}")
        return None
        
    return response.json().get('id')

def create_oid4vp_exchange_template(agency_url, access_token):
    """
    Create exchange template.
    
    Args:
        agency_url: Agency URL
        access_token: Access token for authentication
        
    Returns:
        Template ID
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    template_data = {
        "name": "Identity Verification",
        "description": "Request for identity verification using mobile drivers license",
        "exchange_template": {
            "client_id_prefix": "redirect_uri",
            "request_mode": "by_value_params",
            "exchange_completed_redirect_uri": "uri://completed.redirect",
            "dcql_query": {
                "credentials": [
                    {
                        "id": "mobile_id",
                        "format": "mso_mdoc",
                        "meta": {
                            "doctype_value": "org.iso.18013.5.1.mDL"
                        },
                        "claims": [
                            {
                                "path": ["org.iso.18013.5.1", "family_name"]
                            },
                            {
                                "path": ["org.iso.18013.5.1", "given_name"]
                            },
                            {
                                "path": ["org.iso.18013.5.1", "birth_date"]
                            },
                            {
                                "path": ["org.iso.18013.5.1", "resident_address"]
                            },
                            {
                                "path": ["org.iso.18013.5.1", "resident_city"]
                            },
                            {
                                "path": ["org.iso.18013.5.1", "resident_state"]
                            },
                            {
                                "path": ["org.iso.18013.5.1", "resident_postal_code"]
                            },
                            {
                                "path": ["org.iso.18013.5.1", "resident_country"]
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    response = requests.post(
        f"{agency_url}/v1.0/oidvc/vp/exchange_templates",
        headers=headers,
        json=template_data,
        verify=get_verify_option()
    )
    
    if response.status_code not in [200, 201]:
        print(f"Error creating exchange template: {response.text}")
        return None
        
    return response.json().get('id')

def create_isvdc_issuer_vical_url(vicalBaseUrl, issuer_agent_id) -> str:
    """
    Create ISVDC issuer VICAL URL.
    """

    return f'{vicalBaseUrl}/v1.0/diagency/trust/anchor/{issuer_agent_id}/vical'


def create_trusted_authority(agency_url, access_token, vicalUrl) -> None:
    """
    Create trusted authority.
    
    Args:
        agency_url: Agency URL
        access_token: Access token for authentication
        vicalUrl: VICAL that contains issuer trust anchor cert)
        
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    reg_payload = {
        "name": "string",
        "activated": True,
        "endpoint": vicalUrl,
        "registryType": "vical",
        "entityType": "issuer"
    }

    # Create a reference to a remote registry
    dc_remote_reg_url = f"{agency_url}/v1.0/diagency/trust/remote_providers/registries"
    response = requests.post(
        url=dc_remote_reg_url,
        headers=headers,
        json=reg_payload,
        verify=get_verify_option()
    )
    
    if response.status_code not in [200, 201]:
        print(f"Error creating trust registry: {response.text}")
        return None

    reg_resp = response.json()
    print(f"Successfully created trust registry: {reg_resp}")

    # Now pull the remote registry data
    dc_remote_reg_fetch_url = f"{dc_remote_reg_url}/{reg_resp.get('id')}/fetch"
    print(f"Fetching VICAL data from {dc_remote_reg_fetch_url}")
    response = requests.post(
        url=dc_remote_reg_fetch_url,
        headers=headers,
        verify=get_verify_option()
    )

    if response.status_code not in [200, 201]:
        print(f"Error fetch data from remote registry: {response.text}")
        return None

    reg_resp = response.json()
    print(f"Successfully fetched registry data: {reg_resp}")



def main():
    """Main function to execute the script."""
    # Get agency URLs from environment variables (required)
    agency_url = os.environ.get('AGENCY_URL')
    vical_base_url = os.environ.get('VICAL_BASE_URL')
    oidc_token_endpoint = os.environ.get('OIDC_TOKEN_ENDPOINT')
    
    if not agency_url or not oidc_token_endpoint:
        print("Error: AGENCY_URL and OIDC_TOKEN_ENDPOINT environment variables must be provided.")
        sys.exit(1)
        
    admin_name = os.environ.get('ADMIN_NAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'secret')
    
    # Get tenant admin access token
    print("Getting an access token...")
    admin_access_token = get_access_token(oidc_token_endpoint, admin_name, admin_password)
    
    if not admin_access_token:
        print("Error> failed to obtain an access token.")
        sys.exit(1)
    
    # Create DMV issuer agent
    dmv_agent = create_agent(agency_url, admin_access_token, "", DMV_AGENT_NAME, False, "issuer")
    if dmv_agent is None:
        print("Error> failed to create DMV agent.")
        sys.exit(1)
        
    dmv_agent_id = dmv_agent.get('id')
    dmv_agent_password = dmv_agent.get('client_secret')
    dmv_agent_did = dmv_agent.get('did')
    # dmv_agent_iaca_root_cert = dmv_agent.get('profile', {}).get('issuer', {}).get('root_of_trust', {}).get('x5c', {}).get('certificate')
    
    # Create Bank agent
    bank_agent = create_agent(agency_url, admin_access_token, "", BANK_AGENT_NAME, False, "verifier")
    if bank_agent is None:
        print("Error> failed to create Bank agent.")
        sys.exit(1)
        
    bank_agent_id = bank_agent.get('id')
    bank_agent_password = bank_agent.get('client_secret')
    
    # Generate a DMV access token
    print("Generating DMV access token...")
    dmv_access_token = get_access_token(oidc_token_endpoint, dmv_agent_id, dmv_agent_password)
    if not dmv_access_token:
        print("Error> failed to obtain DMV access token.")
        sys.exit(1)
    
    # Generate a banking access token
    print("Generating Bank access token...")
    bank_access_token = get_access_token(oidc_token_endpoint, bank_agent_id, bank_agent_password)
    if not bank_access_token:
        print("Error> failed to obtain Bank access token.")
        sys.exit(1)
    
    # Create credential schema
    print("Creating credential schema...")
    schema_id = create_oid4vci_credential_schema(agency_url, dmv_access_token)
    if not schema_id:
        print("Error> failed to create credential schema.")
        sys.exit(1)
    print(f"Created credential schema with ID: {schema_id}")
    
    # Create credential definition
    print("Creating credential definition...")
    credential_definition_id = create_oid4vci_credential_definition(agency_url, dmv_access_token, schema_id)
    if not credential_definition_id:
        print("Error> failed to create credential definition.")
        sys.exit(1)
    print(f"Created credential definition with ID: {credential_definition_id}")
    
    # Create exchange template
    print("Creating exchange template...")
    template_id = create_oid4vp_exchange_template(agency_url, bank_access_token)
    if not template_id:
        print("Error> failed to create exchange template.")
        sys.exit(1)
    print(f"Created exchange template with ID: {template_id}")
    
    # Add the issuer to the verifiers trusted authorities list
    print("Adding issuer to the verifiers trusted authorities...")
    issuer_vical_url: str = create_isvdc_issuer_vical_url(vical_base_url, dmv_agent_id)
    issuing_authority = create_trusted_authority(agency_url, admin_access_token, issuer_vical_url)
    issuing_authority_id = issuing_authority.get('id') if issuing_authority else None
    print(f"Created trusted issuing authority with ID: {issuing_authority_id}")
    
    # Get application URLs and credentials from environment variables (required)
    dmv_app_url = os.environ.get('DMV_HOST')
    bank_app_url = os.environ.get('BANK_HOST')
    w3_root_url = os.environ.get('IDP_URL')
    client_id_value = os.environ.get('IDP_CLIENT_ID')
    client_secret_value = os.environ.get('IDP_CLIENT_SECRET')
    is_app_prod_deploy: bool = os.environ.get('IS_APP_PROD_DEPLOY') == 'true'
    node_env_value: str = 'production'
    if not is_app_prod_deploy:
        node_env_value = 'development' 
    
    # Check for required environment variables
    missing_vars = []
    if not dmv_app_url:
        missing_vars.append("DMV_HOST")
    if not bank_app_url:
        missing_vars.append("BANK_HOST")
    if not w3_root_url:
        missing_vars.append("IDP_URL")
    if not client_id_value:
        missing_vars.append("IDP_CLIENT_ID")
    if not client_secret_value:
        missing_vars.append("IDP_CLIENT_SECRET")
    
    if missing_vars:
        print(f"Error: The following required environment variables are missing: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Set redirect URL based on DMV app URL
    dmv_redirect_url = f"{dmv_app_url}/logincallback"

    # If the account URL and token endpoint provided were for localhost, these need to be remapped to internal 
    # docker container network names within the .env file
    if agency_url == "https://localhost:8443/diagency":
        agency_url = "https://iviadcgw:8443/diagency"
    if oidc_token_endpoint == "https://localhost:8443/oauth2/token":
        oidc_token_endpoint = "https://iviadcgw:8443/oauth2/token"
    
    # Create the .env file content
    env_content = f"""# Account and token endpoints
ACCOUNT_URL={agency_url}
REACT_APP_ACCOUNT_URL={agency_url}
REACT_APP_TOKEN_ENDPOINT={oidc_token_endpoint}
NODE_ENV={node_env_value}

# DMV agent configuration
DMV_AGENT_NAME={DMV_AGENT_NAME}
DMV_AGENT_ID={dmv_agent_id}
REACT_APP_DMV_AGENT_ID={dmv_agent_id}
DMV_AGENT_PASSWORD={dmv_agent_password}
REACT_APP_DMV_AGENT_PASSWORD={dmv_agent_password}
DMV_URL={dmv_app_url}
DMV_AGENT_DID={dmv_agent_did}

# Bank agent configuration
BANK_AGENT_NAME={BANK_AGENT_NAME}
BANK_AGENT_ID={bank_agent_id}
REACT_APP_BANK_AGENT_ID={bank_agent_id}
BANK_AGENT_PASSWORD={bank_agent_password}
REACT_APP_BANK_AGENT_PASSWORD={bank_agent_password}
BANK_URL={bank_app_url}

# Authentication configuration
REACT_APP_CLIENT_ID={client_id_value}
REACT_APP_CLIENT_SECRET={client_secret_value}
W3_ROOT={w3_root_url}
REACT_APP_W3_ROOT={w3_root_url}
DMV_REDIRECT_URL={dmv_redirect_url}
REACT_APP_DMV_REDIRECT_URL={dmv_redirect_url}
DMV_LOGOUT_REDIRECT_URL={f"{dmv_app_url}/logout-callback"}
REACT_APP_DMV_LOGOUT_REDIRECT_URL={f"{dmv_app_url}/logout-callback"}

# Credential configuration
CREDENTIAL_SCHEMA_ID={schema_id}
REACT_APP_CREDENTIAL_SCHEMA_ID={schema_id}
CREDENTIAL_DEFINITION_ID={credential_definition_id}
REACT_APP_CREDENTIAL_DEFINITION_ID={credential_definition_id}
EXCHANGE_TEMPLATE_ID={template_id}
REACT_APP_EXCHANGE_TEMPLATE_ID={template_id}"""
    
    # Write the .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n" + open('.env').read())

if __name__ == "__main__":
    main()

# Made with Bob
