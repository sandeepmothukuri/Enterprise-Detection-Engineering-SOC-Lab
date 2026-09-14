#!/usr/bin/env bash
# Generate the local CA and OpenSearch node/admin certificates used by Compose.
set -euo pipefail

CERT_DIR="${1:-config/opensearch/certs}"
mkdir -p "$CERT_DIR"

required_files=(
  root-ca.pem
  opensearch-node1.pem
  opensearch-node1-key.pem
  opensearch-node2.pem
  opensearch-node2-key.pem
  opensearch-admin.pem
  opensearch-admin-key.pem
)

if [[ "${FORCE:-0}" != "1" ]]; then
  complete=1
  for file in "${required_files[@]}"; do
    [[ -s "$CERT_DIR/$file" ]] || complete=0
  done
  if [[ "$complete" == "1" ]]; then
    chmod 644 "$CERT_DIR"/*.pem
    chmod 600 "$CERT_DIR"/*-key.pem
    echo "OpenSearch certificates already exist in $CERT_DIR"
    exit 0
  fi
fi

command -v openssl >/dev/null 2>&1 || {
  echo "openssl is required to generate OpenSearch certificates" >&2
  exit 1
}

umask 077
tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT
pushd "$CERT_DIR" >/dev/null
trap 'rm -rf "$tmp_dir"' EXIT

rm -f root-ca.pem root-ca-key.pem root-ca.srl \
  opensearch-node1.pem opensearch-node1-key.pem \
  opensearch-node2.pem opensearch-node2-key.pem \
  opensearch-admin.pem opensearch-admin-key.pem

cat > root-ca.cnf <<'EOF'
[req]
distinguished_name = req_dn
prompt = no
[req_dn]
CN = SOC Lab Root CA
OU = OpenSearch
O = SOC Lab
L = Hyderabad
ST = Telangana
C = IN
EOF

openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
  -keyout root-ca-key.pem \
  -out root-ca.pem \
  -config root-ca.cnf \
  -addext "basicConstraints=critical,CA:TRUE,pathlen:1" \
  -addext "keyUsage=critical,keyCertSign,cRLSign"

make_certificate() {
  local name="$1" san="$2" eku="$3"
  cat > "${name}.cnf" <<EOF
[req]
distinguished_name = req_dn
prompt = no
[req_dn]
CN = ${name}
OU = OpenSearch
O = SOC Lab
L = Hyderabad
ST = Telangana
C = IN
EOF
  openssl req -nodes -newkey rsa:2048 \
    -keyout "${name}-key.pem" \
    -out "${name}.csr" \
    -config "${name}.cnf"
  printf '%s\n' \
    "basicConstraints=critical,CA:FALSE" \
    "keyUsage=critical,digitalSignature,keyEncipherment" \
    "extendedKeyUsage=${eku}" \
    "subjectAltName=${san}" > "${name}.ext"
  openssl x509 -req -days 825 \
    -in "${name}.csr" \
    -CA root-ca.pem \
    -CAkey root-ca-key.pem \
    -CAcreateserial \
    -out "${name}.pem" \
    -extfile "${name}.ext"
}

make_certificate opensearch-node1 \
  "DNS:opensearch-node1,DNS:localhost,IP:127.0.0.1" \
  "serverAuth,clientAuth"
make_certificate opensearch-node2 \
  "DNS:opensearch-node2,DNS:localhost,IP:127.0.0.1" \
  "serverAuth,clientAuth"
make_certificate opensearch-admin \
  "DNS:opensearch-admin" \
  "clientAuth"

rm -f root-ca.srl root-ca.cnf opensearch-node1.cnf opensearch-node1.csr opensearch-node1.ext \
  opensearch-node2.cnf opensearch-node2.csr opensearch-node2.ext \
  opensearch-admin.cnf opensearch-admin.csr opensearch-admin.ext
chmod 644 ./*.pem
chmod 600 ./*-key.pem
echo "Generated OpenSearch CA and node/admin certificates in $CERT_DIR"
