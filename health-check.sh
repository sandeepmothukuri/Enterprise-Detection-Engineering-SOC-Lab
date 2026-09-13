#!/usr/bin/env bash
# =============================================================================
# Enterprise Detection Engineering SOC Lab — Health Check
# Validates the services that are configured and running.
# =============================================================================
set -u

C_RESET='\033[0m'; C_BOLD='\033[1m'
C_GREEN='\033[0;32m'; C_RED='\033[0;31m'; C_YELLOW='\033[1;33m'
C_CYAN='\033[0;36m'; C_DIM='\033[2m'

PASS=0; FAIL=0; WARN=0

pass() { echo -e "  ${C_GREEN}✔${C_RESET}  ${C_BOLD}$1${C_RESET} — $2"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${C_RED}✗${C_RESET}  ${C_BOLD}$1${C_RESET} — $2"; FAIL=$((FAIL + 1)); }
warn() { echo -e "  ${C_YELLOW}⚠${C_RESET}  ${C_BOLD}$1${C_RESET} — $2"; WARN=$((WARN + 1)); }

http_check() {
  local name="$1" url="$2"
  local code
  code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 8 "$url" 2>/dev/null || true)
  case "$code" in
    200|201|204|301|302|401|403) pass "$name" "HTTP $code — $url" ;;
    *) fail "$name" "HTTP ${code:-000} — $url" ;;
  esac
}

container_check() {
  local name="$1" service="$2"
  local status
  status=$(docker compose ps --status running -q "$service" 2>/dev/null || true)
  if [[ -n "$status" ]]; then
    pass "$name" "service ${service} is running"
  else
    fail "$name" "service ${service} is not running"
  fi
}

echo -e "\n${C_BOLD}${C_CYAN}  Enterprise Detection Engineering SOC Lab — Health Check${C_RESET}"
echo -e "  $(date -u '+%Y-%m-%d %H:%M:%S UTC')\n"

OPENSEARCH_PASSWORD=""
if [[ -f .env ]]; then
  OPENSEARCH_PASSWORD=$(grep '^OPENSEARCH_INITIAL_ADMIN_PASSWORD=' .env | cut -d= -f2- || true)
fi

# Core SIEM
if [[ -n "$OPENSEARCH_PASSWORD" ]]; then
  STATUS=$(curl -sk -u "admin:${OPENSEARCH_PASSWORD}" \
    http://localhost:9200/_cluster/health 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "error")
  DOC_COUNT=$(curl -sk -u "admin:${OPENSEARCH_PASSWORD}" \
    http://localhost:9200/soc-logs-*/_count 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo "?")
  if [[ "$STATUS" == "green" || "$STATUS" == "yellow" ]]; then
    pass "OpenSearch" "cluster:${STATUS} · ${DOC_COUNT} documents"
  else
    fail "OpenSearch" "cluster:${STATUS}"
  fi
else
  http_check "OpenSearch" "http://localhost:9200"
fi

container_check "OpenSearch Node 1" opensearch-node1
container_check "OpenSearch Node 2" opensearch-node2
container_check "Vector Pipeline" vector
http_check "OpenSearch Dashboards" "http://localhost:5601"

# Detection and network sensors
container_check "ElastAlert2" elastalert2
container_check "Zeek" zeek
container_check "Suricata" suricata

# Optional platform services: report status without making the whole check unusable
for item in \
  "DFIR-IRIS|dfir-iris|https://localhost:8443" \
  "MISP|misp|http://localhost:8080" \
  "Velociraptor|velociraptor|https://localhost:8889" \
  "StackStorm|stackstorm|http://localhost:9101" \
  "MITRE Caldera|caldera|http://localhost:8888" \
  "AI Agents|crewai-soc|http://localhost:8500/health" \
  "Ollama|ollama|http://localhost:11434/api/tags" \
  "WebSocket Streamer|ws-streamer|http://localhost:8765"; do
  IFS='|' read -r name service url <<< "$item"
  if docker compose ps --status running -q "$service" >/dev/null 2>&1 && [[ -n "$(docker compose ps --status running -q "$service" 2>/dev/null)" ]]; then
    http_check "$name" "$url"
  else
    warn "$name" "service ${service} is not running"
  fi
done

# Red-team profile is intentionally optional.
if docker compose ps --status running -q responder 2>/dev/null | grep -q .; then
  pass "Responder" "red-team profile is running"
else
  warn "Responder" "optional red-team profile is not running"
fi

echo
echo -e "  ${C_BOLD}Results: ${C_GREEN}${PASS} passed${C_RESET}  ${C_RED}${FAIL} failed${C_RESET}  ${C_YELLOW}${WARN} warnings${C_RESET}"

if [[ $FAIL -gt 0 ]]; then
  echo -e "\n  ${C_YELLOW}${C_BOLD}Core remediation:${C_RESET}"
  echo -e "  ${C_DIM}Validate Compose:${C_RESET} docker compose config --quiet"
  echo -e "  ${C_DIM}Core startup:${C_RESET}    docker compose up -d opensearch-node1 opensearch-node2 vector elastalert2 zeek suricata"
  echo -e "  ${C_DIM}Inspect logs:${C_RESET}     docker compose logs --tail=100 <service>"
  exit 1
fi

echo -e "\n  ${C_GREEN}${C_BOLD}Core lab checks passed.${C_RESET}\n"
exit 0
