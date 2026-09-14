#!/usr/bin/env bash
# Enterprise Detection Engineering SOC Lab — application-level health checks.
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT_DIR"

C_RESET='\033[0m'; C_BOLD='\033[1m'; C_GREEN='\033[0;32m'
C_RED='\033[0;31m'; C_YELLOW='\033[1;33m'; C_CYAN='\033[0;36m'
PASS=0; FAIL=0; WARN=0
pass() { echo -e "  ${C_GREEN}✔${C_RESET} $1 — $2"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${C_RED}✖${C_RESET} $1 — $2"; FAIL=$((FAIL + 1)); }
warn() { echo -e "  ${C_YELLOW}⚠${C_RESET} $1 — $2"; WARN=$((WARN + 1)); }

load_env() {
  [[ -f .env ]] || { fail "Environment" ".env is missing; run ./setup.sh first"; return 1; }
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
}

container_running() {
  local status
  status=$(docker inspect --format='{{.State.Status}}' "$1" 2>/dev/null || echo missing)
  [[ "$status" == running ]]
}

container_check() {
  if container_running "$2"; then pass "$1" "container running"; else fail "$1" "container is not running: $2"; fi
}

http_200() {
  local label="$1" url="$2" code
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "$url" 2>/dev/null || echo 000)
  [[ "$code" == 200 ]] && pass "$label" "HTTP 200 — $url" || fail "$label" "HTTP $code — expected HTTP 200 from $url"
}

https_200() {
  local label="$1" url="$2" ca="$3" code
  [[ -s "$ca" ]] || { fail "$label TLS" "trust chain is missing: $ca"; return; }
  code=$(curl -sS --cacert "$ca" -o /dev/null -w '%{http_code}' --max-time 10 "$url" 2>/dev/null || echo 000)
  [[ "$code" == 200 ]] && pass "$label" "verified HTTPS 200 — $url" || fail "$label" "HTTPS $code — certificate verification or application readiness failed"
}

echo -e "\n${C_BOLD}${C_CYAN}Enterprise Detection Engineering SOC Lab — Health Check${C_RESET}"
echo -e "  $(date -u '+%Y-%m-%d %H:%M:%S UTC')\n"
load_env || exit 1

CA="${ROOT_DIR}/config/opensearch/certs/root-ca.pem"
ADMIN_CERT="${ROOT_DIR}/config/opensearch/certs/opensearch-admin.pem"
ADMIN_KEY="${ROOT_DIR}/config/opensearch/certs/opensearch-admin-key.pem"
IRIS_CA="${ROOT_DIR}/config/iris/iris-ca.pem"
VELOX_CA="${ROOT_DIR}/config/iris/velociraptor-ca.pem"

if [[ -s "$CA" && -s "$ADMIN_CERT" && -s "$ADMIN_KEY" ]]; then
  OS_JSON=$(curl -sS --cacert "$CA" --cert "$ADMIN_CERT" --key "$ADMIN_KEY" --max-time 10 \
    "https://127.0.0.1:${OPENSEARCH_PORT:-9200}/_cluster/health" 2>/dev/null || true)
  STATUS=$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("status","error"))' <<<"$OS_JSON" 2>/dev/null || echo error)
  if [[ "$STATUS" == green || "$STATUS" == yellow ]]; then
    DOC_COUNT=$(curl -sS --cacert "$CA" --cert "$ADMIN_CERT" --key "$ADMIN_KEY" --max-time 10 \
      "https://127.0.0.1:${OPENSEARCH_PORT:-9200}/soc-logs-*/_count" 2>/dev/null \
      | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("count",0))' 2>/dev/null || echo '?')
    pass "OpenSearch" "cluster:${STATUS} · ${DOC_COUNT} documents"
  else
    fail "OpenSearch" "cluster health is ${STATUS}; TLS/authentication may be broken"
  fi
else
  fail "OpenSearch TLS" "generated CA/admin certificate material is missing"
fi

container_check "OpenSearch Node 1" soc-opensearch-1
container_check "OpenSearch Node 2" soc-opensearch-2
http_200 "OpenSearch Dashboards" "http://127.0.0.1:${OPENSEARCH_DASHBOARDS_PORT:-5601}/api/status"
container_check "Vector Pipeline" soc-vector
container_check "Zeek" soc-zeek
container_check "Suricata" soc-suricata
container_check "ElastAlert2" soc-elastalert2

https_200 "DFIR-IRIS" "https://127.0.0.1:${IRIS_PORT:-8443}/" "$IRIS_CA"
http_200 "MISP heartbeat" "http://127.0.0.1:${MISP_PORT:-8080}/users/heartbeat"
https_200 "Velociraptor" "https://127.0.0.1:${VELOCIRAPTOR_PORT:-8889}/" "$VELOX_CA"
container_check "StackStorm" soc-stackstorm

http_200 "MITRE Caldera" "http://127.0.0.1:${CALDERA_PORT:-8888}/"
http_200 "AI Agents API" "http://127.0.0.1:${CREWAI_API_PORT:-8500}/health"
http_200 "Ollama API" "http://127.0.0.1:${OLLAMA_PORT:-11434}/api/tags"
container_check "WebSocket streamer" soc-ws-streamer
http_200 "SOC Portal" "http://127.0.0.1:${SOC_PORT:-80}/"

if container_running soc-responder; then pass "Responder" "optional red-team container running"; else warn "Responder" "optional; not enabled by default"; fi

TOTAL=$((PASS + FAIL + WARN))
echo -e "\n  ${C_BOLD}Results: ${C_GREEN}${PASS} passed${C_RESET}  ${C_RED}${FAIL} failed${C_RESET}  ${C_YELLOW}${WARN} warnings${C_RESET}  (${TOTAL} checks)"
if (( FAIL > 0 )); then
  echo "  docker compose logs --tail=200 <service>"
  echo "  docker compose ps"
  exit 1
fi
echo -e "\n  ${C_GREEN}${C_BOLD}All required service checks passed.${C_RESET}\n"
