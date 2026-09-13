#!/usr/bin/env bash
# End-to-end validation: UDP syslog -> Vector -> OpenSearch.
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

[[ -f .env ]] || { echo "ERROR: .env not found. Run ./setup.sh first." >&2; exit 1; }

PASS=$(grep '^OPENSEARCH_INITIAL_ADMIN_PASSWORD=' .env | cut -d= -f2-)
MARKER="soc-pipeline-test-$(date -u +%Y%m%dT%H%M%SZ)"
INDEX="soc-logs-$(date -u +%Y.%m.%d)"

python3 - "$MARKER" <<'PY'
import socket
import sys
from datetime import datetime, timezone

marker = sys.argv[1]
message = (
    f"<134>1 {datetime.now(timezone.utc).isoformat()}Z soc-test - - - "
    f"SOC_PIPELINE_TEST marker={marker} event_type=authentication_failure "
    f"source_ip=10.10.10.51"
)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(3)
sock.sendto(message.encode(), ("127.0.0.1", 514))
sock.close()
print(f"sent marker={marker}")
PY

for _ in $(seq 1 30); do
  found=$(curl -sk -u "admin:${PASS}" \
    "http://127.0.0.1:9200/${INDEX}/_search?q=message:${MARKER}&size=1" \
    | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("hits",{}).get("total",{}).get("value",0))' 2>/dev/null || echo 0)
  if [[ "$found" != 0 ]]; then
    echo "PASS: Vector -> OpenSearch pipeline delivered ${MARKER}"
    exit 0
  fi
  sleep 1
done

echo "FAIL: marker ${MARKER} was not indexed in ${INDEX}" >&2
echo "Check: docker compose logs --tail=100 vector" >&2
exit 1
