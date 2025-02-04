import os
import shutil
import time
import json
import requests

class Environment:
    JSON_MIME = "application/json"
    buildDir = "./build"
    secretsFilePath = f"{buildDir}/agents_and_client_secrets.txt"

    def __init__(self):
        self.OP_BASE_URL="https://localhost:8443/oauth2"
        self.SERVICE_ADDR="localhost:9720"
        self.PATH_PREFIX="diagency"
        self.ADMIN_CLIENT_ID="admin"
        self.ADMIN_CLIENT_SECRET="secret"
        self.HOLDER_AGENT_ID="cn=user_1,ou=users,dc=ibm,dc=com"
        self.tokens = {}
        self.tokens["admin"] = self.get_access_token(self.ADMIN_CLIENT_ID, self.ADMIN_CLIENT_SECRET)
        self.agents = {}

    def setup_agents_and_tokens(self, is_hyperledger_required: bool = False, num_additional_issuers = 0, num_holders = 1):
        self.SKIP_INDY=not is_hyperledger_required

        # Init the build dir if it isn't already
        if not os.path.exists(self.buildDir):
            os.makedirs(self.buildDir)

        # Get any existing agent secrets from the build dir
        self.agentSecrets = self.get_agent_secrets()

        # Setup our issuer(s)
        if (self.SKIP_INDY):
            issuerName = "issuer"
        else:
            issuerName = "indyIssuer"
        self.create_and_auth_agent("issuer", friendly_name=issuerName)
        for i in range(0, num_additional_issuers):
            self.create_and_auth_agent("issuer", friendly_name=f"{issuerName}_{i + 1}")

        # Setup a verifier
        self.create_and_auth_agent("verifier")

        # Setup our holder(s)
        for i in range(0, num_holders):
            if i == 0:
                index = "holder"
            else:
                index = f"holder{i}"
            username = f"user_{i + 1}"
            self.agents[index] = self.create_agent("holder", id=self.HOLDER_AGENT_ID.replace("user_1", username), name=f"{index}")
            self.tokens[index] = self.get_holder_access_token(username, "secret")

    def create_and_auth_agent(self, agent_type: str, friendly_name: str = None):
        if friendly_name is None:
            friendly_name = agent_type
        self.agents[friendly_name] = self.create_agent(agent_type, name = f"{friendly_name}")
        self.tokens[friendly_name] = self.get_access_token(self.agents[friendly_name]["id"], self.agents[friendly_name]["client_secret"])

    def delete_agents(self):
        if (self.agents == {}):
            existing = self.diagency_get(self.get_admin_token(), f"v1.0/diagency/agents")
            for agent in existing['items']:
                self.delete_agent(agent['id'])
        else:
            for agentKey in self.agents.keys():
                self.delete_agent(self.agents[agentKey]['id'])

    # Assisted by WCA@IBM
    # Latest GenAI contribution: ibm/granite-20b-code-instruct-v2
    def get_admin_token(self):
        return self.tokens["admin"]

    def get_issuer_token(self):
        return self.tokens["issuer"]
    
    def get_issuer_agent_id(self):
        return self.agents["issuer"]["id"]

    def get_holder_token(self):
        return self.tokens["holder"]
    
    def get_holder_agent_id(self):
        return self.agents["holder"]["id"]
    
    def get_verifier_token(self):
        return self.tokens["verifier"]
    
    def get_verifier_agent_id(self):
        return self.agents["verifier"]["id"]
    
    def get_token_for(self, agent_role: str):
        return self.tokens[agent_role]
    
    def get_headers(self, access_token, accept = JSON_MIME): 
        return {
            "Accept": accept, 
            'Content-Type': self.JSON_MIME, 
            "Authorization": f"Bearer {access_token}"
        }

    def get_access_token(self, client_id, client_secret):
        resp = requests.post(f"{self.OP_BASE_URL}/token", headers={"Accept": self.JSON_MIME, "Content-Type": "application/x-www-form-urlencoded"}, verify=False, data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        })
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to obtain access token for: {client_id} / {client_secret}")
        return resp.json()['access_token']

    def get_holder_access_token(self, username, password):
        resp = requests.post(f"{self.OP_BASE_URL}/token", headers={"Accept": self.JSON_MIME, "Content-Type": "application/x-www-form-urlencoded"}, verify=False, data={
            "grant_type": "password",
            "client_id": "onpremise_vcholders",
            "username": username,
            "password": password
        })
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to obtain access token for: {username} / {password}")
        return resp.json()['access_token']

    def get_url(self, path):
        return f"https://{self.SERVICE_ADDR}/{self.PATH_PREFIX}/{path}"

    def diagency_delete(self, access_token, path, expected_status = 204):
        print(f"\n\nDELETE {self.get_url(path)}")
        resp = requests.delete(self.get_url(path), headers=self.get_headers(access_token), verify=False)
        assert resp.status_code == expected_status
        print(f"\nResponse: {resp.status_code}\n")

    def diagency_patch(self, access_token, path, body, expected_status = 200, accept = JSON_MIME):
        print(f"\n\nPATCH {self.get_url(path)}\n{json.dumps(body, indent=4)}")
        api_resp = requests.patch(self.get_url(path), headers=self.get_headers(access_token, accept), verify=False, json=body)
        return self.handle_api_response(api_resp, accept, expected_status)

    def diagency_post(self, access_token, path, body, expected_status = 201, accept = JSON_MIME):
        print(f"\n\nPOST {self.get_url(path)}\n{json.dumps(body, indent=4)}")
        api_resp = requests.post(self.get_url(path), headers=self.get_headers(access_token, accept), verify=False, json=body)
        return self.handle_api_response(api_resp, accept, expected_status)

    def diagency_put(self, access_token, path, body, expected_status = 200, accept = JSON_MIME):
        print(f"\n\nPUT {self.get_url(path)}\n{json.dumps(body, indent=4)}")
        api_resp = requests.put(self.get_url(path), headers=self.get_headers(access_token, accept), verify=False, json=body)
        return self.handle_api_response(api_resp, accept, expected_status)

    def diagency_get(self, access_token, path, expected_status = 200, accept = JSON_MIME):
        print(f"\n\nGET {self.get_url(path)}")
        api_resp = requests.get(self.get_url(path), headers=self.get_headers(access_token, accept), verify=False)
        return self.handle_api_response(api_resp, accept, expected_status)
    
    def handle_api_response(self, api_resp, accept: str, expected_status: int):
        if accept == self.JSON_MIME:
            print(f"\nResponse: {api_resp.status_code}:\n{json.dumps(api_resp.json(), indent=4)}\n")
            resp = api_resp.json()
        else:
            content_type = api_resp.headers.get('Content-Type')
            print(f"\nResponse: {api_resp.status_code} - {content_type}")
            if api_resp.status_code >= 200 and api_resp.status_code < 300:
                assert content_type == accept
            resp = api_resp
        assert api_resp.status_code == expected_status
        return resp

    def create_agent(self, type, id = "", name = ""):
        try:
            filter = { "name": name }
            existingAgentMetadata = self.get_if_resource_exists(self.get_admin_token(), "v1.0/diagency/agents", filter)
            if existingAgentMetadata is not None:
                existingAgent = self.diagency_get(self.get_admin_token(), f"v1.0/diagency/agents/{existingAgentMetadata['id']}")
                if existingAgent["agent_type"] == "issuer" or existingAgent["agent_type"] == "verifier":
                    existingAgent["client_secret"] = self.agentSecrets[existingAgent["id"]]
                return existingAgent
        except AssertionError:
            # The assertion failure from the above indicates the fetch failed 
            # and is an indicator we should instead be creating the agent afresh
            pass

        if name == "":
            name = f"{type}"
        agent_body = {
            "id": id,
            "name": name,
            "agent_type": type
        }

        if self.SKIP_INDY:
            agent_body["did_method"] = "did:web"
            agent_body["is_did_on_ledger"] = False
        else:
            agent_body["did_method"] = "did:indy"
            agent_body["is_did_on_ledger"] = True

        result = self.diagency_post(self.get_admin_token(), "v1.0/diagency/agents", agent_body, 200)
        self.write_agent_to_secrets_file(result)
        return result

    def delete_agent(self, id):
        self.diagency_delete(self.get_admin_token(), f"v1.0/diagency/agents/{id}", 200)

    def assert_obj(self, created_obj, resp_obj):
        for attr in created_obj.keys():
            assert created_obj[attr] == resp_obj[attr]

    def assert_no_indy(self, resp_obj):
        assert "indy" not in resp_obj

    def wait_for_state(self, state: str, token: str, url: str, seconds: int = 10):
        return self.wait_for_states([state], token, url, seconds)

    def wait_for_states(self, states: list[str], token: str, url: str, seconds: int = 10):
        resp = self.diagency_get(token, url)
        for i in range(0, seconds + 1):
            if resp["state"] in states:
                break
            else:
                time.sleep(1)
                resp = self.diagency_get(token, url)
        assert resp["state"] in states
        return resp
    
    def connect_holder_to(self, agent_role: str):
        invitation = self.diagency_post(self.get_token_for(agent_role), "v1.0/diagency/invitations", {
            "direct_route": True,
            "type": "connection"
        }, 200)
        url = invitation["url"]

        connection = self.diagency_post(self.get_holder_token(), "v1.0/diagency/connections", {
            "url": url
        }, 200)
        connection_id = connection["id"]
        assert connection["state"] == "outbound_offer"

        # Poll to make sure the connection is connected
        connection = self.wait_for_state("connected", self.get_holder_token(), f"v1.0/diagency/connections/{connection_id}")

        return {
            "localDid": connection["local"]["pairwise"]["did"],
            "remoteDid": connection["remote"]["pairwise"]["did"]
        }

    def delete_all_connections(self, agent_role: str):
        connections = self.diagency_get(self.get_token_for(agent_role), "v1.0/diagency/connections")
        for conn in connections["items"]:
            self.diagency_delete(self.get_token_for(agent_role), f"v1.0/diagency/connections/{conn['id']}", 200)

    def get_if_resource_exists(self, access_token, url, filter = None):
        try:
            if filter is not None:
                url = url + f"?filter={json.dumps(filter)}"
            existing = self.diagency_get(access_token, url)
            if (existing['count'] != 0):
                resource = existing['items'][0]
                print(f"\nGetting existing resource: {json.dumps(resource, indent=4)}")
                return resource
        except AssertionError:
            # The assertion failure from the above indicates the fetch failed 
            pass
        return None
    
    def cleanup(self):
        self.delete_agents()
        self.delete_agent_secrets()

    def get_agent_secrets(self):
        result = {}
        if os.path.exists(self.secretsFilePath):
            try:
                with open(self.secretsFilePath) as file:
                    for line in file:
                        arr = line.rstrip().split(' | ')
                        result[arr[0]] = arr[1]
            except Exception as e:
                print(f"An error occurred when trying to read from the agent secrets file: {e}")
                exit(1)
        return result
        
    def write_agent_to_secrets_file(self, agent):
        if 'client_secret' in agent:
            try:
                with open(self.secretsFilePath, "a") as file:
                    file.write(f"{agent['id']} | {agent['client_secret']}\n")
                    file.close()
            except Exception as e:
                print(f"An error occurred when trying to write to the agent secrets file: {e}")
                exit(1)
    
    def delete_agent_secrets(self):
        if os.path.exists(self.buildDir):
            try:
                shutil.rmtree(self.buildDir)
            except Exception as e:
                print(f"An error occurred when trying to delete the agent secrets file: {e}")
                exit(1)
