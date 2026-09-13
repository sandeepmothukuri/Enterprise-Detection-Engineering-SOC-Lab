#!/usr/bin/env bash
# =============================================================================
# Enterprise Detection Engineering SOC Lab — Setup
# Prepares credentials, validates configuration, starts the core detection path,
# and leaves optional services available for explicit follow-up startup.
# =============================================================================
set -euo pipefail

C_RESET='\033[0m'; C_BOLD='\033[1m'; C_GREEN='\033[0;32m'
C_YELLOW='\033[1;33m'; C_RED='\033[0;31m'; C_CYAN='\033[0;36m'

ok()   { echo -e "${C_GREEN}  ✔${C_RESET}  $*"; }
info() { echo -e "${C_CYAN}  →${C_RESET}  $*"; }
warn() { echo -e "${C_YELLOW}  ⚠${C_RESET}  $*"; }
fail() { echo -e "${C_RED}  ✗${C_RESET}  $*" >&2; exit 1; }
step() { echo -e "\n${C_BOLD}${C_CYAN}── $* ──${C_RESET}"; }

step "Preflight"
command -v docker >/dev/null 2>&1 || fail "Docker is not installed"
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required"
command -v openssl >/dev/null 2>&1 || fail "OpenSSL is required"
command -v curl >/dev/null 2>&1 || fail "curl is required"
ok "Docker $(docker --version | awk '{print $3}' | tr -d ',')"
ok "Docker Compose $(docker compose version --short)"

TOTAL_RAM_KB=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)
TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
if (( TOTAL_RAM_GB < 14 )); then
  warn "${TOTAL_RAM_GB}GB RAM detected; 16GB+ is recommended for the full stack"
else
  ok "${TOTAL_RAM_GB}GB RAM available"
fi

step "Environment"
if [[ ! -f .env ]]; then
  cp .env.example .env
  sed -i "s/^OPENSEARCH_INITIAL_ADMIN_PASSWORD=.*/OPENSEARCH_INITIAL_ADMIN_PASSWORD=$(openssl rand -hex 16)/" .env
  sed -i "s/^IRIS_SECRET_KEY=.*/IRIS_SECRET_KEY=$(openssl rand -hex 32)/" .env
  sed -i "s/^IRIS_DB_PASSWORD=.*/IRIS_DB_PASSWORD=$(openssl rand -hex 16)/" .env
  sed -i "s/^MISP_DB_PASSWORD=.*/MISP_DB_PASSWORD=$(openssl rand -hex 16)/" .env
  sed -i "s/^MISP_MYSQL_ROOT_PASSWORD=.*/MISP_MYSQL_ROOT_PASSWORD=$(openssl rand -hex 16)/" .env
  sed -i "s/^ST2_AUTH_TOKEN=.*/ST2_AUTH_TOKEN=$(openssl rand -hex 20)/" .env
  ok ".env created with generated local credentials"
else
  ok ".env already exists"
fi

required=(OPENSEARCH_INITIAL_ADMIN_PASSWORD IRIS_SECRET_KEY IRIS_ADMIN_PASSWORD IRIS_DB_PASSWORD MISP_DB_PASSWORD MISP_ADMIN_PASSWORD ST2_AUTH_TOKEN)
for var in "${required[@]}"; do
  value=$(grep -E "^${var}=" .env | cut -d= -f2- || true)
  [[ -n "${value//\"/}" && "$value" != CHANGE_ME* ]] || fail "${var} must be set in .env"
done
ok "Required credentials are populated"

step "Compose validation"
docker compose config --quiet
ok "docker-compose.yml is syntactically valid"

step "Core configuration validation"
docker compose run --rm --no-deps vector validate --config /etc/vector/vector.toml >/dev/null
ok "Vector configuration validated"

docker run --rm \
  -v "$PWD/config/zeek:/opt/zeek/share/zeek/site:ro" \
  zeek/zeek:8.2.2 \
  zeek -C /opt/zeek/share/zeek/site/local.zeek >/tmp/zeek-config-check.log
ok "Zeek configuration compiled successfully"

step "Core services"
docker compose up -d opensearch-node1 opensearch-node2

PASSWORD=$(grep '^OPENSEARCH_INITIAL_ADMIN_PASSWORD=' .env | cut -d= -f2-)
for _ in $(seq 1 60); do
  status=$(curl -sk -u "admin:${PASSWORD}" http://127.0.0.1:9200/_cluster/health 2>/dev/null \
    | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status","red"))' 2>/dev/null || echo red)
  if [[ "$status" == green || "$status" == yellow ]]; then
    ok "OpenSearch cluster: ${status}"
    break
  fi
  sleep 1
done
[[ "$status" == green || "$status" == yellow ]] || fail "OpenSearch did not become healthy"

docker compose up -d opensearch-dashboards vector elastalert2 zeek suricata
ok "Core SIEM, detection and network sensors started"

step "Validation"
./health-check.sh

cat <<'EOF'

Next:
  1. Run the real pipeline test:     ./tools/test-pipeline.sh
  2. Run the Zeek T1046 test:        ./tools/test-zeek-t1046.sh
  3. Start optional platforms:       docker compose up -d misp dfir-iris velociraptor caldera stackstorm ollama crewai-soc ws-streamer nginx
  4. Start the red-team profile:     docker compose --profile redteam up -d responder

Do not use `docker compose down -v` during normal testing; it deletes persistent lab data.
EOF
