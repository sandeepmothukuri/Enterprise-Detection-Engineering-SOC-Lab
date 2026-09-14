#!/usr/bin/env bash
# Live validation of the custom Zeek T1046 detector.
set -euo pipefail

NETWORK="${SOC_DOCKER_NETWORK:-$(docker network ls --format '{{.Name}}' | grep -E 'enterprise-detection-engineering-soc-lab.*_soc-net$' | head -1)}"
TARGET_NAME="soc-t1046-target"

[[ -n "$NETWORK" ]] || { echo "ERROR: SOC Docker network not found. Start the core Compose stack first." >&2; exit 1; }

ZEEK_CONTAINER="$(docker compose ps -q zeek 2>/dev/null || true)"
[[ -n "$ZEEK_CONTAINER" ]] || {
  echo "ERROR: Zeek service is not running. Start it with: docker compose up -d zeek" >&2
  exit 1
}
ZEEK_STATUS="$(docker inspect --format='{{.State.Status}}' "$ZEEK_CONTAINER" 2>/dev/null || true)"
[[ "$ZEEK_STATUS" == "running" ]] || {
  echo "ERROR: Zeek container is not running (status: ${ZEEK_STATUS:-unknown})." >&2
  exit 1
}

docker rm -f "$TARGET_NAME" >/dev/null 2>&1 || true

docker run -d --name "$TARGET_NAME" --network "$NETWORK" python:3.12-alpine \
  python -m http.server 8080 --bind 0.0.0.0 >/dev/null

cleanup() { docker rm -f "$TARGET_NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

TARGET_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$TARGET_NAME")
[[ -n "$TARGET_IP" ]] || { echo "ERROR: target container did not receive an IP." >&2; exit 1; }

echo "Testing Zeek T1046 against ${TARGET_IP} on ${NETWORK}"

echo "Generating 25 TCP connection attempts to distinct destination ports..."
docker run --rm --network "$NETWORK" python:3.12-alpine python - "$TARGET_IP" <<'PY'
import socket
import sys
import time

target = sys.argv[1]
for port in range(10000, 10025):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.15)
    try:
        sock.connect((target, port))
    except OSError:
        pass
    finally:
        sock.close()
    time.sleep(0.03)
PY

for _ in $(seq 1 20); do
  if docker exec "$ZEEK_CONTAINER" sh -c 'grep -h "Port_Scan\|T1046" /opt/zeek/logs/notice.log 2>/dev/null | tail -20' | grep -q .; then
    echo "PASS: Zeek emitted a T1046 Port_Scan notice."
    exit 0
  fi
  sleep 1
done

echo "FAIL: no T1046 notice was observed in Zeek notice.log" >&2
echo "Inspect: docker compose logs --tail=100 zeek" >&2
echo "Inspect: docker exec ${ZEEK_CONTAINER} sh -c 'tail -50 /opt/zeek/logs/conn.log'" >&2
exit 1
