from scenarios.MdocMdlScenario import MdocMdlScenario
from data.mdoc_jsonld_mdl import MDOC_JSONLD_MDL_CONTEXTS, MDOC_MDL_ATTRIBUTES, MDOC_MDL_DOCTYPE

class MdocMdlAamva(MdocMdlScenario):
    def getDocType(self):
        return MDOC_MDL_DOCTYPE

    def get_short_name(self):
        return "USA Mobile Driver's License"

    def get_schema(self):
        schema = MDOC_JSONLD_MDL_CONTEXTS
        schema["org.iso.18013.5.1.aamva:domestic_driving_privileges"] = {
            '@id': 'org.iso.18013.5.1.aamva:domestic_driving_privileges',
            '@type': 'schema:Thing'
        }
        schema["org.iso.18013.5.1.aamva:family_name_truncation"] = {
            '@id': 'org.iso.18013.5.1.aamva:family_name_truncation',
            '@type': 'schema:Text'
        }
        schema["org.iso.18013.5.1.aamva:given_name_truncation"] = {
            '@id': 'org.iso.18013.5.1.aamva:given_name_truncation',
            '@type': 'schema:Text'
        }
        schema["org.iso.18013.5.1.aamva:sex"] = {
            '@id': 'org.iso.18013.5.1.aamva:sex',
            '@type': 'schema:Number'
        }
        schema["org.iso.18013.5.1.aamva:DHS_compliance"] = {
            '@id': 'org.iso.18013.5.1.aamva:DHS_compliance',
            '@type': 'schema:Text'
        }
        return schema

    def get_attributes_for_credential(self):
        cred = MDOC_MDL_ATTRIBUTES
        cred["org.iso.18013.5.1.aamva:domestic_driving_privileges"] = {
            "domestic_vehicle_class": {
                "domestic_vehicle_class_code": "D",
                "domestic_vehicle_class_description": "Sedan < 12,000 lb.",
            }
        }
        cred["org.iso.18013.5.1.aamva:family_name_truncation"] = "N"
        cred["org.iso.18013.5.1.aamva:given_name_truncation"] = "N"
        cred["org.iso.18013.5.1.aamva:sex"] = 1
        cred["org.iso.18013.5.1.aamva:DHS_compliance"] = "N"
        return cred
    
    def get_attribute_preview_for_credential(self):
        cred = {
            "@type": "https://didcomm.org/issue-credential/1.0/credential-preview",
            "attributes": [
                {
                    "name": "org.iso.18013.5.1.aamva:DHS_compliance",
                    "value": "N"
                }
            ]
        }
        return cred

    def get_disclosure_field(self):
        return "$['org.iso.18013.5.1.aamva']['DHS_compliance']"