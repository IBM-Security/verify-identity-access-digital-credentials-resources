#!/bin/bash

OP_PRIVATE_KEY=op_server_priv.key
OP_PUBLIC_CERT=op_server_pub.crt
DB_CERT=iviadcdb_ca.pem

rm -f $OP_PRIVATE_KEY
rm -f $OP_PUBLIC_CERT

openssl req -x509 -newkey rsa:4096 -keyout $OP_PRIVATE_KEY -out $OP_PUBLIC_CERT -days 365 -config req.conf -nodes

echo
echo "Public key certificate: "
echo

openssl x509 -in $OP_PUBLIC_CERT -text

python <<EOF
import base64
f = open('provider.template', 'r')
provider_template = f.read()
f.close()
f = open('$OP_PRIVATE_KEY', 'rb')
op_key = base64.b64encode(f.read()).decode()
f.close()
f = open('$OP_PUBLIC_CERT', 'rb')
op_crt = base64.b64encode(f.read()).decode()
f.close()
f = open('$DB_CERT', 'rb')
db_crt = base64.b64encode(f.read()).decode()
macros = {
    "$OP_PRIVATE_KEY": op_key,
    "$OP_PUBLIC_CERT": op_crt,
    "$DB_CERT": db_crt
}
print(provider_template)
print(macros)
for key in macros:
    print(key)
    provider_template = provider_template.replace('<' + key + '>', macros[key])
f = open('provider.yml', 'w')
f.write(provider_template)
f.close()
EOF

TARGET_CA=iviadcop_ca.pem
cp -f ${OP_PUBLIC_CERT} ../config/${TARGET_CA}
cp -f ${OP_PUBLIC_CERT} ../iag_config/${TARGET_CA}
