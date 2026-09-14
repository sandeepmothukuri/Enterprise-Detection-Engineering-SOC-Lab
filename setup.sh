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

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

set_env_value() {
  local key="$1" value="$2"
  if grep -qE "^${key}=" .env 2>/dev/null; then
    python3 - "$key" "$value" <<'PY'
from pathlib import Path
import sys
key, value = sys.argv[1:]
path = Path('.env')
lines = path.read_text().splitlines()
out = []
for line in lines:
    if line.startswith(key + '='):
        out.append(f'{key}={value}')
    else:
        out.append(line)
path.write_text('\n'.join(out) + '\n')
PY
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}

random_hex() { openssl rand -hex "$1"; }

[[ "$(id -u)" -eq 0 || "${SOC_SETUP_NO_SUDO:-0}" == "1" || -w /proc/sys/vm/max_map_count ]] || warn "Run with sudo if vm.max_map_count needs changing."

require_cmd docker
require_cmd openssl
require_cmd curl
require_cmd python3

docker info >/dev/null 2>&1 || die "Docker daemon is not available. Start Docker Desktop/Docker Engine first."
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required."

info "Checking system resources"
MEM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0)
[[ "$MEM_MB" -ge 12000 ]] || warn "Detected ${MEM_MB} MiB RAM; 16 GiB is recommended for the full lab."
DISK_GB=$(df -Pk . | awk 'NR==2 {print int($4/1024/1024)}')
[[ "$DISK_GB" -ge 30 ]] || warn "Less than 30 GiB free in the repository filesystem."
ok "Docker, Compose and local prerequisites detected"

info "Preparing local .env"
if [[ ! -f .env ]]; then
  cp .env.example .env
  ok "Created .env from .env.example"
fi

# Replace placeholder secrets on first setup. Values already set by the user are preserved.
for item in \
  "OPENSEARCH_INITIAL_ADMIN_PASSWORD:24" \
  "ST2_AUTH_TOKEN:20" \
  "IRIS_SECRET_KEY:32" \
  "IRIS_ADM_API_KEY:32" \
  "IRIS_DB_PASSWORD:24" \
  "MISP_ADMIN_PASSWORD:24" \
  "MISP_DB_PASSWORD:24" \
  "MISP_MYSQL_ROOT_PASSWORD:24" \
  "VELOX_PASSWORD:24" \
  "CALDERA_API_KEY_RED:20" \
  "CALDERA_API_KEY_BLUE:20" \
  "CALDERA_RED_PASS:24" \
  "CALDERA_BLUE_PASS:24"; do
  key="${item%%:*}" bytes="${item##*:}"
  current=$(grep -E "^${key}=" .env | cut -d= -f2- || true)
  if [[ -z "$current" || "$current" == CHANGE_ME* ]]; then
    set_env_value "$key" "$(random_hex "$bytes")"
  fi
done

# Preserve the canonical local service endpoints used by the stack.
set_env_value OPENSEARCH_PORT "${OPENSEARCH_PORT:-9200}"
set_env_value OPENSEARCH_DASHBOARDS_PORT "${OPENSEARCH_DASHBOARDS_PORT:-5601}"
set_env_value CREWAI_API_PORT "${CREWAI_API_PORT:-8500}"
set_env_value SOC_PORT "${SOC_PORT:-80}"

if grep -q '^MISP_API_KEY=$' .env; then
  warn "MISP_API_KEY is empty; setup will provision a fresh MISP admin API key after MISP becomes ready."
fi

info "Applying Linux kernel setting required by OpenSearch"
CURRENT_MAP=$(sysctl -n vm.max_map_count 2>/dev/null || echo 0)
if [[ "$CURRENT_MAP" -lt 262144 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    sudo sysctl -w vm.max_map_count=262144 >/dev/null
  elif [[ -w /proc/sys/vm/max_map_count ]]; then
    sysctl -w vm.max_map_count=262144 >/dev/null
  else
    die "vm.max_map_count must be at least 262144 for OpenSearch."
  fi
fi
ok "vm.max_map_count=$(sysctl -n vm.max_map_count)"

info "Generating local OpenSearch certificates"
bash tools/generate-opensearch-certs.sh
ok "OpenSearch TLS material is ready (generated files are Git-ignored)"

info "Validating Compose before startup"
docker compose --env-file .env config --quiet
ok "docker compose config"

info "Creating persistent data directories"
mkdir -p data/opensearch-node1 data/opensearch-node2 data/misp data/iris data/velociraptor data/stackstorm data/caldera logs

info "Pulling images"
docker compose --env-file .env pull
ok "Images pulled"

info "Starting the SOC stack (red-team profile remains disabled)"
docker compose --env-file .env up -d

wait_for_health() {
  local attempts=0 max_attempts=180
  while (( attempts < max_attempts )); do
    if bash health-check.sh >/tmp/soc-health-check.log 2>&1; then
      cat /tmp/soc-health-check.log
      return 0
    fi
    attempts=$((attempts + 1))
    printf '\r  Waiting for service readiness: %d/%d' "$attempts" "$max_attempts"
    sleep 2
  done
  echo
  cat /tmp/soc-health-check.log >&2 || true
  return 1
}

info "Waiting for application-level readiness"
if ! wait_for_health; then
  die "Critical service readiness checks did not pass. Review: docker compose logs --tail=200"
fi
ok "Critical services report healthy"

# The official MISP image supports generating/resetting the admin API key after initialization.
# This is performed only when no key was supplied by the operator.
MISP_KEY=$(grep '^MISP_API_KEY=' .env | cut -d= -f2- || true)
if [[ -z "$MISP_KEY" ]]; then
  info "Provisioning a fresh MISP admin API key"
  NEW_MISP_KEY=$(docker exec -i soc-misp bash -lc \
    'cd /var/www/MISP && sudo -u www-data /var/www/MISP/app/Console/cake user change_authkey 1' \
    2>/dev/null | awk -F': ' '/new key created/ {print $2}' | tail -1 || true)
  if [[ -n "$NEW_MISP_KEY" ]]; then
    set_env_value MISP_API_KEY "$NEW_MISP_KEY"
    ok "MISP admin API key provisioned locally"
  else
    warn "MISP API key could not be provisioned automatically; MISP enrichment remains disabled until MISP_API_KEY is set."
  fi
fi

# Start the configured Ollama model only after the API is ready.
if docker compose ps -q ollama >/dev/null 2>&1; then
  MODEL=$(grep '^OLLAMA_MODEL=' .env | cut -d= -f2- || echo 'llama3.2:3b')
  info "Ensuring Ollama model ${MODEL} is available"
  docker exec soc-ollama ollama pull "$MODEL" >/dev/null 2>&1 || warn "Ollama model pull failed; run: docker exec soc-ollama ollama pull ${MODEL}"
fi

info "Running final health validation"
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
