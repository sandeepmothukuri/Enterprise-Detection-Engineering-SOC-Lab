#!/usr/bin/env bash
# Generate deterministic local OpenSearch TLS material before the OpenSearch
# containers start. Generated material is intentionally ignored by Git.
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

# Never leave a partially generated PKI set behind.
rm -f "$CERT_DIR"/*.pem "$CERT_DIR"/*.csr "$CERT_DIR"/*.ext "$CERT_DIR"/*.srl

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

# OpenSearch Security requires PKCS#8 private keys for PEM configuration.
for name in opensearch-node1 opensearch-node2 opensearch-admin; do
  openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt \
    -in "$CERT_DIR/${name}-key.pem" \
    -out "$CERT_DIR/${name}-key-pkcs8.pem"
  mv "$CERT_DIR/${name}-key-pkcs8.pem" "$CERT_DIR/${name}-key.pem"
done

rm -f "$CERT_DIR/root-ca.srl"

# Public certificates are readable by the OpenSearch container. Private keys
# remain local and untracked; keep them readable only by the generating user.
chmod 644 "$CERT_DIR"/root-ca.pem "$CERT_DIR"/opensearch-*.pem
chmod 600 "$CERT_DIR"/root-ca-key.pem "$CERT_DIR"/opensearch-*-key.pem

# Validate the generated certificate/key set before allowing Compose startup.
openssl verify -CAfile "$CERT_DIR/root-ca.pem" \
  "$CERT_DIR/opensearch-node1.pem" \
  "$CERT_DIR/opensearch-node2.pem" \
  "$CERT_DIR/opensearch-admin.pem" >/dev/null

for name in opensearch-node1 opensearch-node2 opensearch-admin; do
  cert_pub=$(openssl x509 -in "$CERT_DIR/${name}.pem" -pubkey -noout | openssl pkey -pubin -outform DER | sha256sum | cut -d' ' -f1)
  key_pub=$(openssl pkey -in "$CERT_DIR/${name}-key.pem" -pubout | openssl pkey -pubin -outform DER | sha256sum | cut -d' ' -f1)
  [[ "$cert_pub" == "$key_pub" ]] || {
    echo "ERROR: certificate/key mismatch for ${name}." >&2
    exit 1
  }
done

echo "Generated and validated OpenSearch CA, node and admin certificates in $CERT_DIR"
