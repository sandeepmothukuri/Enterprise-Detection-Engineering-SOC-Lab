#!/usr/bin/env bash
# Enterprise Detection Engineering SOC Lab — reproducible local bootstrap.
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT_DIR"

C_RESET='\033[0m'; C_BOLD='\033[1m'; C_GREEN='\033[0;32m'
C_RED='\033[0;31m'; C_YELLOW='\033[1;33m'; C_CYAN='\033[0;36m'
info() { echo -e "  ${C_CYAN}→${C_RESET} $1"; }
ok() { echo -e "  ${C_GREEN}✔${C_RESET} $1"; }
warn() { echo -e "  ${C_YELLOW}⚠${C_RESET} $1"; }
die() { echo -e "  ${C_RED}✖${C_RESET} $1" >&2; exit 1; }
require_cmd() { command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"; }

set_env_value() {
  local key="$1" value="$2"
  python3 - "$key" "$value" <<'PY'
from pathlib import Path
import sys
key, value = sys.argv[1:]
path = Path('.env')
lines = path.read_text().splitlines() if path.exists() else []
out = []
found = False
for line in lines:
    if line.startswith(key + '='):
        out.append(f'{key}={value}')
        found = True
    else:
        out.append(line)
if not found:
    out.append(f'{key}={value}')
path.write_text('\n'.join(out) + '\n')
PY
}

random_hex() { openssl rand -hex "$1"; }
require_cmd docker; require_cmd openssl; require_cmd curl; require_cmd python3
docker info >/dev/null 2>&1 || die "Docker daemon is not available."
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required."

MEM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0)
[[ "$MEM_MB" -ge 12000 ]] || warn "Detected ${MEM_MB} MiB RAM; 16 GiB is recommended."

if [[ ! -f .env ]]; then
  cp .env.example .env
  ok "Created .env from .env.example"
fi

for item in \
  "OPENSEARCH_INITIAL_ADMIN_PASSWORD:24" "ST2_AUTH_TOKEN:20" "IRIS_SECRET_KEY:32" \
  "IRIS_ADM_API_KEY:32" "IRIS_ADMIN_PASSWORD:24" "IRIS_DB_PASSWORD:24" \
  "MISP_ADMIN_PASSWORD:24" "MISP_DB_PASSWORD:24" "MISP_MYSQL_ROOT_PASSWORD:24" \
  "VELOX_PASSWORD:24" "CALDERA_API_KEY_RED:20" "CALDERA_API_KEY_BLUE:20" \
  "CALDERA_RED_PASS:24" "CALDERA_BLUE_PASS:24"; do
  key="${item%%:*}" bytes="${item##*:}"
  current=$(grep -E "^${key}=" .env | cut -d= -f2- || true)
  if [[ -z "$current" || "$current" == CHANGE_ME* ]]; then
    set_env_value "$key" "$(random_hex "$bytes")"
  fi
done

CURRENT_MAP=$(sysctl -n vm.max_map_count 2>/dev/null || echo 0)
if [[ "$CURRENT_MAP" -lt 262144 ]]; then
  if command -v sudo >/dev/null 2>&1; then sudo sysctl -w vm.max_map_count=262144 >/dev/null
  elif [[ -w /proc/sys/vm/max_map_count ]]; then sysctl -w vm.max_map_count=262144 >/dev/null
  else die "vm.max_map_count must be at least 262144."; fi
fi
ok "vm.max_map_count=$(sysctl -n vm.max_map_count)"

bash tools/generate-opensearch-certs.sh
mkdir -p data/opensearch-node1 data/opensearch-node2 data/misp data/iris data/velociraptor data/stackstorm data/caldera logs config/iris

# Caldera does not interpolate shell variables in its YAML. Render the ignored
# runtime configuration from the tracked template before the container starts.
sed \
  -e "s|__CALDERA_RED_PASS__|${CALDERA_RED_PASS}|g" \
  -e "s|__CALDERA_BLUE_PASS__|${CALDERA_BLUE_PASS}|g" \
  -e "s|__CALDERA_API_KEY_RED__|${CALDERA_API_KEY_RED}|g" \
  -e "s|__CALDERA_API_KEY_BLUE__|${CALDERA_API_KEY_BLUE}|g" \
  config/caldera/local.yml.template > config/caldera/local.yml
chmod 600 config/caldera/local.yml

# Compose must be valid before any containers are started.
docker compose --env-file .env config --quiet
ok "docker compose config"

docker compose --env-file .env pull

# Start services that do not depend on runtime certificates extracted from an
# application container. AI/portal startup happens after the IRIS CA exists.
docker compose --env-file .env up -d \
  opensearch-node1 opensearch-node2 opensearch-dashboards vector elastalert2 \
  st-mongo st-rabbitmq stackstorm iris-db dfir-iris misp-db misp-redis misp \
  velociraptor caldera ollama

wait_http() {
  local url="$1" attempts=0 max=120
  while (( attempts < max )); do
    if curl -ksf --max-time 5 "$url" >/dev/null 2>&1; then return 0; fi
    attempts=$((attempts + 1)); sleep 2
  done
  return 1
}

info "Waiting for OpenSearch, IRIS, MISP and Velociraptor readiness"
wait_http "https://127.0.0.1:${OPENSEARCH_PORT:-9200}/_cluster/health" || die "OpenSearch REST endpoint did not become reachable."
wait_http "https://127.0.0.1:${IRIS_PORT:-8443}/" || die "DFIR-IRIS did not become reachable."
wait_http "http://127.0.0.1:${MISP_PORT:-8080}/users/heartbeat" || die "MISP did not become reachable."
wait_http "https://127.0.0.1:${VELOCIRAPTOR_PORT:-8889}/" || die "Velociraptor did not become reachable."
ok "Core application endpoints are reachable"

# Trust the locally generated IRIS server certificate without disabling TLS
# verification in the AI or portal containers. The resulting file is ignored.
rm -f config/iris/iris-ca.pem
openssl s_client -connect "127.0.0.1:${IRIS_PORT:-8443}" -servername dfir-iris -showcerts </dev/null 2>/dev/null \
  | awk '/-----BEGIN CERTIFICATE-----/{capture=1} capture{print} /-----END CERTIFICATE-----/{exit}' \
  > config/iris/iris-ca.pem
[[ -s config/iris/iris-ca.pem ]] || die "Could not capture the DFIR-IRIS TLS certificate."
chmod 644 config/iris/iris-ca.pem
ok "Captured DFIR-IRIS local trust certificate"

# Provision a MISP admin API key if the operator did not supply one.
MISP_KEY=$(grep '^MISP_API_KEY=' .env | cut -d= -f2- || true)
if [[ -z "$MISP_KEY" ]]; then
  NEW_MISP_KEY=$(docker exec -i soc-misp bash -lc \
    'cd /var/www/MISP && sudo -u www-data /var/www/MISP/app/Console/cake user change_authkey 1' \
    2>/dev/null | awk -F': ' '/new key created/ {print $2}' | tail -1 || true)
  [[ -n "$NEW_MISP_KEY" ]] && set_env_value MISP_API_KEY "$NEW_MISP_KEY" || warn "MISP API key could not be provisioned automatically."
fi

# Now the AI and portal mounts have the CA material they need.
docker compose --env-file .env up -d crewai-soc ws-streamer nginx

info "Waiting for final application readiness"
for attempt in $(seq 1 120); do
  if bash health-check.sh >/tmp/soc-health-check.log 2>&1; then
    cat /tmp/soc-health-check.log
    break
  fi
  if [[ "$attempt" == 120 ]]; then
    cat /tmp/soc-health-check.log >&2 || true
    die "Critical health checks did not pass."
  fi
  printf '\r  Waiting for service readiness: %s/120' "$attempt"
  sleep 2
done
echo

MODEL=$(grep '^OLLAMA_MODEL=' .env | cut -d= -f2- || echo 'llama3.2:3b')
docker exec soc-ollama ollama pull "$MODEL" >/dev/null 2>&1 || warn "Ollama model pull failed; run: docker exec soc-ollama ollama pull ${MODEL}"

bash health-check.sh
cat <<EOF

${C_BOLD}${C_GREEN}SOC Lab setup completed.${C_RESET}

Next validation steps:
  ./health-check.sh
  ./simulate-attack.sh apt29
  ./simulate-attack.sh verify
  ./tools/validate-detections.sh

Core endpoints:
  OpenSearch          https://127.0.0.1:${OPENSEARCH_PORT:-9200}
  Dashboards          http://127.0.0.1:${OPENSEARCH_DASHBOARDS_PORT:-5601}
  DFIR-IRIS           https://127.0.0.1:${IRIS_PORT:-8443}
  MISP                http://127.0.0.1:${MISP_PORT:-8080}
  Velociraptor        https://127.0.0.1:${VELOCIRAPTOR_PORT:-8889}
  Caldera             http://127.0.0.1:${CALDERA_PORT:-8888}
  AI Agents API       http://127.0.0.1:${CREWAI_API_PORT:-8500}
  Ollama              http://127.0.0.1:${OLLAMA_PORT:-11434}
EOF
