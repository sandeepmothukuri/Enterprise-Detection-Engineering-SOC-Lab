#!/usr/bin/env bash
# Live validation of the custom Zeek T1046 detector.
set -euo pipefail

NETWORK="${SOC_DOCKER_NETWORK:-$(docker network ls --format '{{.Name}}' | grep -E 'enterprise-detection-engineering-soc-lab.*_soc-net$' | head -1)}"
TEST_ZEEK_NAME="soc-t1046-zeek"
ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

if command -v cygpath >/dev/null 2>&1; then
  ROOT_DIR="$(cygpath -m "$ROOT_DIR")"
  export MSYS_NO_PATHCONV=1
fi

[[ -n "$NETWORK" ]] || { echo "ERROR: SOC Docker network not found. Start the core Compose stack first." >&2; exit 1; }

docker rm -f "$TEST_ZEEK_NAME" >/dev/null 2>&1 || true

cleanup() {
  docker rm -f "$TEST_ZEEK_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker run -d --name "$TEST_ZEEK_NAME" --network "$NETWORK" \
  --cap-add NET_ADMIN --cap-add NET_RAW \
  -v "$ROOT_DIR/config/zeek:/usr/local/zeek/share/zeek/site:ro" \
  -v "${TEST_ZEEK_NAME}-logs:/usr/local/zeek/logs" \
  --workdir /usr/local/zeek/logs \
  zeek/zeek:8.2.2 \
  sh -c 'python3 -m http.server 8080 --bind 127.0.0.1 >/tmp/t1046-http.log 2>&1 & exec zeek -i lo -C local /usr/local/zeek/share/zeek/policy/tuning/json-logs.zeek' >/dev/null

echo "Testing Zeek T1046 with live loopback traffic in ${NETWORK}"
sleep 3

echo "Generating 25 TCP connection attempts to distinct destination ports..."
docker exec -i "$TEST_ZEEK_NAME" python3 - <<'PY'
import socket
import time

for port in range(10000, 10025):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.15)
    try:
        sock.connect(("127.0.0.1", port))
    except OSError:
        pass
    finally:
        sock.close()
    time.sleep(0.03)
PY

for _ in $(seq 1 20); do
  if docker exec "$TEST_ZEEK_NAME" sh -c 'grep -h "Port_Scan\|T1046" /usr/local/zeek/logs/notice.log 2>/dev/null | tail -20' | grep -q .; then
    echo "PASS: Zeek emitted a T1046 Port_Scan notice."
    exit 0
  fi
  sleep 1
done

echo "FAIL: no T1046 notice was observed in Zeek notice.log" >&2
echo "Inspect: docker logs --tail=100 ${TEST_ZEEK_NAME}" >&2
echo "Inspect: docker exec ${TEST_ZEEK_NAME} sh -c 'tail -50 /usr/local/zeek/logs/conn.log'" >&2
exit 1
