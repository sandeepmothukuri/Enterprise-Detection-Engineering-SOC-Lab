#!/usr/bin/env bash
# Enterprise Detection Engineering SOC Lab — application-level health checks.
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT_DIR"

C_RESET='\033[0m'; C_BOLD='\033[1m'
C_GREEN='\033[0;32m'; C_RED='\033[0;31m'; C_YELLOW='\033[1;33m'
C_CYAN='\033[0;36m'
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
  local name="$1"
  local status
  status=$(docker inspect --format='{{.State.Status}}' "$name" 2>/dev/null || echo missing)
  [[ "$status" == running ]]
}

container_check() {
  local label="$1" name="$2"
  if container_running "$name"; then
    pass "$label" "container running"
  else
    fail "$label" "container is not running: $name"
  fi
}

http_200() {
  local label="$1" url="$2"
  local code
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "$url" 2>/dev/null || echo 000)
  if [[ "$code" == 200 ]]; then
    pass "$label" "HTTP 200 — $url"
  else
    fail "$label" "HTTP $code — expected HTTP 200 from $url"
  fi
}

https_200() {
  local label="$1" url="$2"
  local code
  code=$(curl -sS -k -o /dev/null -w '%{http_code}' --max-time 10 "$url" 2>/dev/null || echo 000)
  if [[ "$code" == 200 ]]; then
    pass "$label" "HTTPS 200 — $url"
  else
    fail "$label" "HTTPS $code — expected HTTP 200 from $url"
  fi
}

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "\n${C_BOLD}${C_CYAN}Enterprise Detection Engineering SOC Lab — Health Check${C_RESET}"
echo -e "  $(date -u '+%Y-%m-%d %H:%M:%S UTC')\n"

if ! load_env; then
  exit 1
fi

# ── OpenSearch ────────────────────────────────────────────────────────────────
CA="${ROOT_DIR}/config/opensearch/certs/root-ca.pem"
ADMIN_CERT="${ROOT_DIR}/config/opensearch/certs/opensearch-admin.pem"
ADMIN_KEY="${ROOT_DIR}/config/opensearch/certs/opensearch-admin-key.pem"

if [[ -s "$CA" && -s "$ADMIN_CERT" && -s "$ADMIN_KEY" ]]; then
  OS_JSON=$(curl -sS --cacert "$CA" --cert "$ADMIN_CERT" --key "$ADMIN_KEY" \
    --max-time 10 "https://127.0.0.1:${OPENSEARCH_PORT:-9200}/_cluster/health" 2>/dev/null || true)
  STATUS=$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("status","error"))' <<<"$OS_JSON" 2>/dev/null || echo error)
  if [[ "$STATUS" == green || "$STATUS" == yellow ]]; then
    DOC_COUNT=$(curl -sS --cacert "$CA" --cert "$ADMIN_CERT" --key "$ADMIN_KEY" \
      --max-time 10 "https://127.0.0.1:${OPENSEARCH_PORT:-9200}/soc-logs-*/_count" 2>/dev/null \
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

# ── Investigation / enrichment ────────────────────────────────────────────────
https_200 "DFIR-IRIS" "https://127.0.0.1:${IRIS_PORT:-8443}/"
http_200 "MISP heartbeat" "http://127.0.0.1:${MISP_PORT:-8080}/users/heartbeat"
https_200 "Velociraptor" "https://127.0.0.1:${VELOCIRAPTOR_PORT:-8889}/"
container_check "StackStorm" soc-stackstorm

# ── Adversary emulation / AI ──────────────────────────────────────────────────
http_200 "MITRE Caldera" "http://127.0.0.1:${CALDERA_PORT:-8888}/"
http_200 "AI Agents API" "http://127.0.0.1:${CREWAI_API_PORT:-8500}/health"
http_200 "Ollama API" "http://127.0.0.1:${OLLAMA_PORT:-11434}/api/tags"
container_check "WebSocket streamer" soc-ws-streamer
http_200 "SOC Portal" "http://127.0.0.1:${SOC_PORT:-80}/"

# ── Optional red team ─────────────────────────────────────────────────────────
if container_running soc-responder; then
  pass "Responder" "optional red-team container running"
else
  warn "Responder" "optional; not running unless the redteam profile is explicitly enabled"
fi

TOTAL=$((PASS + FAIL + WARN))
echo
echo -e "  ${C_BOLD}Results: ${C_GREEN}${PASS} passed${C_RESET}  ${C_RED}${FAIL} failed${C_RESET}  ${C_YELLOW}${WARN} warnings${C_RESET}  (${TOTAL} checks)"

if (( FAIL > 0 )); then
  echo
  echo "Critical remediation examples:"
  echo "  docker compose logs --tail=200 <service>"
  echo "  docker compose ps"
  exit 1
fi

echo -e "\n  ${C_GREEN}${C_BOLD}All required service checks passed.${C_RESET}\n"
