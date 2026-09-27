#!/usr/bin/env bash
# =============================================================================
# Automated End-to-End SOC Detection & Pipeline Test Harness Wrapper
# =============================================================================
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-offline}"
OPENSEARCH_URL="${2:-http://localhost:9200}"
OPENSEARCH_PASS=""

if [[ -f .env ]]; then
  OPENSEARCH_PASS=$(grep '^OPENSEARCH_INITIAL_ADMIN_PASSWORD=' .env | cut -d= -f2- || true)
fi

python3 tools/test-e2e-harness.py --mode "$MODE" --opensearch-url "$OPENSEARCH_URL" --opensearch-password "$OPENSEARCH_PASS"
