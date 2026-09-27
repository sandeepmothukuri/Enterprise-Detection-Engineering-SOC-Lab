#!/usr/bin/env bash
# =============================================================================
# OpenSearch Dashboards NDJSON Import Utility
# =============================================================================
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

DASHBOARDS_URL="${1:-http://localhost:5601}"
NDJSON_FILE="${2:-dashboards/opensearch_dashboards_export.ndjson}"
OPENSEARCH_PASS=""

if [[ -f .env ]]; then
  OPENSEARCH_PASS=$(grep '^OPENSEARCH_INITIAL_ADMIN_PASSWORD=' .env | cut -d= -f2- || true)
fi

AUTH_HEADER=()
if [[ -n "$OPENSEARCH_PASS" ]]; then
  AUTH_HEADER=(-u "admin:${OPENSEARCH_PASS}")
fi

if [[ ! -f "$NDJSON_FILE" ]]; then
  echo "[-] Error: NDJSON file not found: $NDJSON_FILE" >&2
  exit 1
fi

echo "[*] Importing pre-configured SOC dashboards into ${DASHBOARDS_URL}..."
echo "[*] Source file: ${NDJSON_FILE}"

HTTP_CODE=$(curl -sk "${AUTH_HEADER[@]}" \
  -X POST "${DASHBOARDS_URL}/api/saved_objects/_import?overwrite=true" \
  -H "osd-xsrf: true" \
  --form file=@"${NDJSON_FILE}" \
  -o /tmp/osd_import_resp.json \
  -w "%{http_code}" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
  echo "[+] SUCCESS: Pre-configured SOC Dashboards successfully imported into OpenSearch Dashboards!"
  cat /tmp/osd_import_resp.json
  echo
else
  echo "[-] Notice: OpenSearch Dashboards responded with HTTP ${HTTP_CODE}."
  if [[ -f /tmp/osd_import_resp.json ]]; then
    cat /tmp/osd_import_resp.json
    echo
  fi
  echo "[!] Ensure OpenSearch Dashboards is running at ${DASHBOARDS_URL} before importing."
fi
