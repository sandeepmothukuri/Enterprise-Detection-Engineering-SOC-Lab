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

# Convert MSYS paths to Windows paths for openssl (native Windows binary)
# openssl on Windows/MSYS requires Windows-style paths
win_test_dir="$(cygpath -w "$TEST_DIR" 2>/dev/null || echo "$TEST_DIR")"

# Use Windows openssl with Windows paths
/mingw64/bin/openssl.exe verify \
  -CAfile "$win_test_dir\\root-ca.pem" \
  "$win_test_dir\\opensearch-node1.pem" \
  "$win_test_dir\\opensearch-node2.pem" \
  "$win_test_dir\\opensearch-admin.pem"

for name in opensearch-node1 opensearch-node2 opensearch-admin; do
  subject="$("/mingw64/bin/openssl.exe" x509 -in "$win_test_dir\\$name.pem" -noout -subject)"
  grep -Fq "CN=$name" <<<"$subject"
done

"$ROOT_DIR/tools/generate-opensearch-certs.sh" "$TEST_DIR" | grep -Fq "already exist"
echo "OpenSearch certificate generation test passed"