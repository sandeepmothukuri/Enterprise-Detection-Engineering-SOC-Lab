#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"' EXIT

"$ROOT_DIR/tools/generate-opensearch-certs.sh" "$TEST_DIR"

for file in \
  root-ca.pem \
  opensearch-node1.pem opensearch-node1-key.pem \
  opensearch-node2.pem opensearch-node2-key.pem \
  opensearch-admin.pem opensearch-admin-key.pem; do
  [[ -s "$TEST_DIR/$file" ]] || {
    echo "missing generated certificate: $file" >&2
    exit 1
  }
done

openssl verify -CAfile "$TEST_DIR/root-ca.pem" \
  "$TEST_DIR/opensearch-node1.pem" \
  "$TEST_DIR/opensearch-node2.pem" \
  "$TEST_DIR/opensearch-admin.pem"

for name in opensearch-node1 opensearch-node2 opensearch-admin; do
  subject="$(openssl x509 -in "$TEST_DIR/$name.pem" -noout -subject)"
  grep -Fq "CN=$name" <<<"$subject"
done

"$ROOT_DIR/tools/generate-opensearch-certs.sh" "$TEST_DIR" | grep -Fq "already exist"
echo "OpenSearch certificate generation test passed"
