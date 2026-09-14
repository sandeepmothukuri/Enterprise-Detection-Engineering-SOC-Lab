#!/usr/bin/env bash
# Generate local, self-signed OpenSearch certificates for the SOC lab.
# Generated material is intentionally ignored by Git.
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CERT_DIR="$ROOT_DIR/config/opensearch/certs"
DAYS="${OPENSEARCH_CERT_DAYS:-825}"

command -v openssl >/dev/null 2>&1 || {
  echo "ERROR: openssl is required to generate OpenSearch certificates." >&2
  exit 1
}

mkdir -p "$CERT_DIR"
umask 077

required=(
  root-ca.pem root-ca-key.pem
  opensearch-node1.pem opensearch-node1-key.pem
  opensearch-node2.pem opensearch-node2-key.pem
  opensearch-admin.pem opensearch-admin-key.pem
)

all_present=true
for file in "${required[@]}"; do
  [[ -s "$CERT_DIR/$file" ]] || all_present=false
done

if $all_present; then
  echo "OpenSearch certificates already exist: $CERT_DIR"
  exit 0
fi

rm -f "$CERT_DIR"/*.pem "$CERT_DIR"/*.csr "$CERT_DIR"/*.srl

openssl req -x509 -newkey rsa:4096 -sha256 -days "$DAYS" -nodes \
  -keyout "$CERT_DIR/root-ca-key.pem" \
  -out "$CERT_DIR/root-ca.pem" \
  -subj "/C=IN/ST=Telangana/L=Hyderabad/O=SOC Lab/OU=OpenSearch/CN=SOC Lab Root CA"

make_cert() {
  local name="$1"
  local cn="$2"
  local san="$3"
  local eku="$4"

  openssl req -new -newkey rsa:2048 -nodes -sha256 \
    -keyout "$CERT_DIR/${name}-key.pem" \
    -out "$CERT_DIR/${name}.csr" \
    -subj "/C=IN/ST=Telangana/L=Hyderabad/O=SOC Lab/OU=OpenSearch/CN=${cn}"

  cat > "$CERT_DIR/${name}.ext" <<EOF
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=${eku}
subjectAltName=${san}
EOF

  openssl x509 -req -sha256 -days "$DAYS" \
    -in "$CERT_DIR/${name}.csr" \
    -CA "$CERT_DIR/root-ca.pem" \
    -CAkey "$CERT_DIR/root-ca-key.pem" \
    -CAcreateserial \
    -out "$CERT_DIR/${name}.pem" \
    -extfile "$CERT_DIR/${name}.ext"

  rm -f "$CERT_DIR/${name}.csr" "$CERT_DIR/${name}.ext"
}

make_cert "opensearch-node1" "opensearch-node1" \
  "DNS:opensearch-node1,DNS:localhost,IP:127.0.0.1,IP:172.20.0.10" \
  "serverAuth,clientAuth"

make_cert "opensearch-node2" "opensearch-node2" \
  "DNS:opensearch-node2,DNS:localhost,IP:127.0.0.1,IP:172.20.0.11" \
  "serverAuth,clientAuth"

make_cert "opensearch-admin" "opensearch-admin" \
  "DNS:opensearch-admin" \
  "clientAuth"

rm -f "$CERT_DIR/root-ca.srl"

# OpenSearch runs as a non-root user in the official image. The certificate
# files are public material; the private keys remain local and untracked.
chmod 644 "$CERT_DIR"/*.pem
chmod 644 "$CERT_DIR"/*-key.pem

echo "Generated OpenSearch CA, node and admin certificates in $CERT_DIR"
