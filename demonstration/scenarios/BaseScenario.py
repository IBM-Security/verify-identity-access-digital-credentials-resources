from config.Environment import Environment

class BaseScenario:
    ##############################################################
    # Child test_ classes need to implement all of these methods #
    ##############################################################
    def create_credential_schema(self, env: Environment):
        raise NotImplementedError()

    def create_credential_definition(self, env: Environment, credSchemaId: str):
        raise NotImplementedError()
    
    def get_attributes_for_credential(self):
        raise NotImplementedError()
    
    def get_attribute_preview_for_credential(self):
        raise NotImplementedError()
    
    def get_verification_proof_request_args(self, credSchema: object):
        raise NotImplementedError()

    def is_v1_credschemadefs(self):
        raise NotImplementedError()
    
    # Optionally, callers may need to override this
    def is_hyperledger_required(self):
        return False
    
    def get_trusted_issuing_authority_args(self, issuer_agent) -> list[dict]:
        return []
    
    def get_proof_schema_requested_attributes(self, env: Environment):
        return {}
    
    def get_expected_verification_state(self):
        return "passed"
    
    ##############################################################

    def configure_trusted_issuing_authorities(self, env: Environment): 
        trust_cfg = self.get_trusted_issuing_authority_args(env.agents["issuer"])
        if len(trust_cfg) == 0:
            return
        
        for cfg in trust_cfg: 
            resp = env.diagency_post(env.get_verifier_token(), "v1.0/diagency/trusted_issuing_authorities", cfg)
        
    def get_credential_body(self, credDefId: str, addressedToDid: str):
        body = {
            "state": "outbound_offer",
            "to": {
                "did": addressedToDid
            },
            "attributes": self.get_attributes_for_credential(),
            "properties": {},
            "credential_definition_id": credDefId,
        }
        return body
    
    def get_verification_request_body(self, credSchema: object, addressedToDid, proof_schema_id: str = None, store_presentation: str = None):
        post_body = {
            "state": "outbound_proof_request",
            "properties": {},
            "proof_request": self.get_verification_proof_request_args(credSchema)
        }
        if addressedToDid:
            post_body["to"] = {
                "did": addressedToDid
            }
        if proof_schema_id:
            post_body["proof_schema_id"] = proof_schema_id
        if store_presentation:
            post_body["store_presentation"] = store_presentation
        return post_body
    
    def create_proof_schema(self, env: Environment, credSchema: object):
        requested_attributes = self.get_proof_schema_requested_attributes(env)
        if len(requested_attributes) == 0:
            print("This credential format doesn't require proof schemas")
            return

        resp = env.diagency_post(env.get_verifier_token(), "v1.0/diagency/proof_schemas", {
            "name": credSchema("schema_name"),
            "version": credSchema("schema_version"),
            "requested_attributes": requested_attributes,
            "requested_predicates": {}
        }, 200)

        return resp
        
    def issuer_create_cred_offer(self, env: Environment, credDefId: str, to: str):
        body = self.get_credential_body(credDefId, to)
        offer = env.diagency_post(env.get_token_for("issuer"), "v1.0/diagency/credentials", body, 200)
        return offer
        
    def holder_accept_cred_offer(self, env: Environment, offerId: str): 
        resp = env.diagency_patch(env.get_token_for("holder"), f"v1.0/diagency/credentials/{offerId}", {
            "state": "accepted"
        })
        assert resp["state"] == "stored"
        return resp

    def verifier_initiate_verification(self, env: Environment, credSchema: object, to: str):
        body = self.get_verification_request_body(credSchema, to)
        resp = env.diagency_post(env.get_token_for("verifier"), "v1.0/diagency/verifications", body, 200)
        return resp

    def holder_proof_generated(self, env: Environment, verificationId: str):
        resp = env.diagency_patch(env.get_token_for("holder"), f"v1.0/diagency/verifications/{verificationId}", {
            "state": "proof_generated"
        })
        return resp

    def holder_wait_for_proof_generated(self, env: Environment, verificationId: str):
        resp = env.wait_for_state("proof_generated", env.get_token_for("holder"), f"v1.0/diagency/verifications/{verificationId}")

        # Ensure the holder has some info about what is going to be shared with the verifier
        assert "info" in resp.keys()

    def holder_proof_shared(self, env: Environment, verificationId: str):
        resp = env.diagency_patch(env.get_token_for("holder"), f"v1.0/diagency/verifications/{verificationId}", {
            "state": "proof_shared"
        })
        return resp

    def wait_for_verification_state(self, env: Environment, agent_role: str, verificationId: str):
        resp = env.wait_for_states(["passed", "failed"], env.get_token_for(agent_role), f"v1.0/diagency/verifications/{verificationId}")
        assert resp["state"] == self.get_expected_verification_state()

    def execute(self, env: Environment, scenario: str, do_issuance: bool = True, do_verification: bool = True, do_deleteAgents: bool = False):
        if (do_deleteAgents):
            env.cleanup()
            print("Deleted all agents and associated data. Exiting...")
            return

        # Setup agents (issuer, verifier, holder)
        env.setup_agents_and_tokens(self.is_hyperledger_required())

        # Setup agent connections (issuer-holder, holder-verifier)
        holderToIssuerConn = env.connect_holder_to("issuer")
        holderToVerifierConn = env.connect_holder_to("verifier")
        holderDidForIssuer = holderToIssuerConn["localDid"]
        holderDidForVerifier = holderToVerifierConn["localDid"]

        # Create credential schema
        credSchema = self.create_credential_schema(env)

        # Create credential definition
        credDefinition = self.create_credential_definition(env, credSchema.get("id"))

        # Create proof schema (if applicable)
        proofSchema = self.create_proof_schema(env, credSchema)

        # Configure trusted auths (if applicable)
        self.configure_trusted_issuing_authorities(env)

        # Start credential issuance flow (Pre-connected issuer-initiated scenario for simplicity)
        if (do_issuance):
            offer = self.issuer_create_cred_offer(env, credDefinition["id"], holderDidForIssuer)
            self.holder_accept_cred_offer(env, offer["id"])

        # Start credential verification flow (Pre-connected verifier-initiated scenario for simplicity)
        if (do_verification):
            verificationRequest = self.verifier_initiate_verification(env, credSchema, holderDidForVerifier)
            self.holder_proof_generated(env, verificationRequest["id"])
            self.holder_wait_for_proof_generated(env, verificationRequest["id"])
            self.holder_proof_shared(env, verificationRequest["id"])
            self.wait_for_verification_state(env, "holder", verificationRequest["id"])
            self.wait_for_verification_state(env, "verifier", verificationRequest["id"])

        # Print summary of script output
        print(f"\nDemonstration summary ({scenario}):")
        print(f"===================================")
        print(f"Agent client secrets are available at {env.secretsFilePath}")
        print(f"Used credential schema with id {credSchema['id']}")
        print(f"Used credential definition with id {credDefinition['id']}")
        if (do_issuance):
            print(f"Performed credential issuance:\n\t |_ Issuer agent with id {env.get_issuer_agent_id()} offered a credential to holder agent id {env.get_holder_agent_id()}\n\t |_ The holder accepted the offer and was issued a credential with id {offer['id']}")
        if (do_verification):
            print(f"Performed credential verification:\n\t |_ Verifier agent with id {env.get_verifier_agent_id()} requested a proof from holder agent id {env.get_holder_agent_id()}\n\t |_ The holder generated and presented a valid proof. The associated verification's id was {verificationRequest['id']}")
