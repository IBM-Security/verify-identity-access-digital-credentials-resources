MDOC_MDL_DOCTYPE = "org.iso.18013.5.1.mDL"

# A JSON-LD representation of some of the minimum required attributes for a mDL
MDOC_JSONLD_MDL_CONTEXTS={
    "schema": "http://schema.org/",
    "org.iso.18013.5.1:family_name": {
        "@id": "org.iso.18013.5.1:family_name",
        "@type": "schema:Text"
    },
    "org.iso.18013.5.1:given_name": {
        "@id": "org.iso.18013.5.1:given_name",
        "@type": "schema:Text"
    },
    "org.iso.18013.5.1:birth_date": {
        "@id": "org.iso.18013.5.1:birth_date",
        "@type": "schema:Date"
    },
    "org.iso.18013.5.1:issue_date": {
        "@id": "org.iso.18013.5.1:issue_date",
        "@type": "schema:Date"
    },
    "org.iso.18013.5.1:expiry_date": {
        "@id": "org.iso.18013.5.1:expiry_date",
        "@type": "schema:Date"
    },
    "org.iso.18013.5.1:issuing_country": {
        "@id": "org.iso.18013.5.1:issuing_country",
        "@type": "schema:Text"
    },
    "org.iso.18013.5.1:issuing_authority": {
        "@id": "org.iso.18013.5.1:issuing_authority",
        "@type": "schema:Text"
    },
    "org.iso.18013.5.1:document_number": {
        "@id": "org.iso.18013.5.1:document_number",
        "@type": "schema:Text"
    },
    "org.iso.18013.5.1:portrait": {
        "@id": "org.iso.18013.5.1:portrait",
        "@type": "schema:ImageObject"
    },
    "org.iso.18013.5.1:driving_privileges": {
        "@id": "org.iso.18013.5.1:driving_privileges",
        "@type": "schema:ItemList"
    },
    "org.iso.18013.5.1:un_distinguishing_sign": {
        "@id": "org.iso.18013.5.1:un_distinguishing_sign",
        "@type": "schema:Text"
    }
}

MDOC_MDL_ATTRIBUTES={
    'org.iso.18013.5.1:family_name': 'Smith',
    'org.iso.18013.5.1:given_name': 'John',
    'org.iso.18013.5.1:birth_date': '1980-01-01',
    'org.iso.18013.5.1:issue_date': '2024-01-01',
    'org.iso.18013.5.1:expiry_date': '2029-01-01',
    'org.iso.18013.5.1:issuing_country': 'US',
    'org.iso.18013.5.1:issuing_authority': 'IBM Department of Transport',
    'org.iso.18013.5.1:document_number': '123456789',
    'org.iso.18013.5.1:portrait': [ 0x01, 0x02 ],
    'org.iso.18013.5.1:driving_privileges': [
        {
            "vehicle_category_code": "A",
            "issue_date": '2024-01-01',
            "expiry_date": '2029-01-01'
        }
    ],
    'org.iso.18013.5.1:un_distinguishing_sign': 'US',
}

MDOC_MDL_ATTRIBUTES_PREVIEW = {
    "@type": "https://didcomm.org/issue-credential/1.0/credential-preview",
    "attributes": [
        {
            "name": "org.iso.18013.5.1:family_name",
            "value": "Smith"
        },
        {
            "name": "org.iso.18013.5.1:given_name",
            "value": "John"
        },
        {
            "name": "org.iso.18013.5.1:birth_date",
            "value": "1980-01-01"
        },
        {
            "name": "org.iso.18013.5.1:issue_date",
            "value": "2024-01-01"
        },
        {
            "name": "org.iso.18013.5.1:expiry_date",
            "value": "2029-01-01"
        },
        {
            "name": "org.iso.18013.5.1:issuing_country",
            "value": "US"
        },
        {
            "name": "org.iso.18013.5.1:issuing_authority",
            "value": "IBM Department of Transport"
        },
        {
            "name": "org.iso.18013.5.1:document_number",
            "value": "123456789"
        },
        # NOTE: According to the spec: https://github.com/hyperledger/aries-rfcs/tree/main/features/0036-issue-credential#preview-credential
        #       When mime-type is not undefined, the 'value' field is supposed to be a base64url-encoded string representing a binary BLOB.
        #       but currently the holder just sends this attribute preview verbatim to an issuer,
        #       and we don't do any further processing on it (because the issuer is meant to manually create an offer based on it)
        {
            "name": "org.iso.18013.5.1:portrait",
            "mime-type": "application/json",
            "value": [ 0x01, 0x02 ]
        },
        {
            "name": "org.iso.18013.5.1:driving_privileges",
            "mime-type": "application/json",
            "value": [
                {
                    "vehicle_category_code": "A",
                    "issue_date": '2024-01-01',
                    "expiry_date": '2029-01-01'
                }
            ]
        },
        {
            "name": "org.iso.18013.5.1:un_distinguishing_sign",
            "value": "US"
        },
    ]
}
