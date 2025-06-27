from scenarios.BaseScenario import BaseScenario
from config.Environment import Environment
from data.mdoc_jsonld_mdl import MDOC_JSONLD_MDL_CONTEXTS, MDOC_MDL_ATTRIBUTES, MDOC_MDL_ATTRIBUTES_PREVIEW, MDOC_MDL_DOCTYPE

class MdocMdlScenario(BaseScenario):
    def getDocType(self):
        return MDOC_MDL_DOCTYPE
    
    def get_short_name(self):
        return "Mobile Driver's License"
    
    def get_schema(self):
        return MDOC_JSONLD_MDL_CONTEXTS
    
    def get_disclosure_field(self):
        return "$['org.iso.18013.5.1']['driving_privileges']"
    
    def get_attributes_for_credential(self):
        return MDOC_MDL_ATTRIBUTES
    
    def get_attribute_preview_for_credential(self):
        return MDOC_MDL_ATTRIBUTES_PREVIEW

    def create_credential_schema(self, env: Environment):
        filter = { 'name': self.get_short_name() }
        existingSchema = env.get_if_resource_exists(env.get_issuer_token(), "v2.0/diagency/credential_schemas", filter)
        if (existingSchema is None):
            return env.diagency_post(env.get_issuer_token(), "v2.0/diagency/credential_schemas", {
                "name": f"{self.get_short_name()}",
                "version": "4.2",
                "contexts": {
                    '@context': self.get_schema()
                }
            })
        else:
            print(f"Using existing schema with id {existingSchema['id']}...")
            return existingSchema

    def create_credential_definition(self, env: Environment, credSchemaId):
        filter = { 'schema.id': credSchemaId }
        existingDefinition = env.get_if_resource_exists(env.get_issuer_token(), "v2.0/diagency/credential_definitions", filter)
        if (existingDefinition is None):
            created_obj = {
                "schema_id": credSchemaId,
                "credential_document_type": [ self.getDocType() ],
                "credential_format": "mso_mdoc", 
                "cryptographic_binding_methods": [ "did:key" ],
                "key_proof_types": {
                    "jwt": [ "EdDSA" ]
                },
                "credential_signing_algorithm": "EdDSA"
            }
            resp = env.diagency_post(env.get_issuer_token(), "v2.0/diagency/credential_definitions", created_obj)
            env.assert_obj(created_obj, resp)
            env.assert_no_indy(resp)
            return resp
        else:
            print(f"Using existing cred def with id {existingDefinition['id']}...")
            return existingDefinition

    def get_trusted_issuing_authority_args(self, credDef):
        certificate = credDef["mso_mdoc"]["certificate"]
        return [{
            "credential_document_type": self.getDocType(),
            "certificate": certificate,
        }]

    def get_verification_proof_request_args(self, credSchema: object):
        return {
            "name": credSchema["name"],
            "version": credSchema["version"],
            "mso_mdoc": {
                "presentation_definition": {
                    "id": "123",
                    "input_descriptors": [
                        {
                            "id": self.getDocType(),
                            "format": {
                                "mso_mdoc": {
                                    "alg": ['EdDSA', 'ES256']
                                }
                            },
                            "name": f"{self.get_short_name()} Card",
                            "purpose": f'Must have a valid {self.get_short_name()} card',
                            "constraints": {
                                "limit_disclosure": 'required',
                                "fields": [{
                                    "path": [ self.get_disclosure_field() ],
                                    "intent_to_retain": False,
                                }]
                            }
                        }
                    ]
                }
            }
        }

    def is_v1_credschemadefs(self):
        raise False

