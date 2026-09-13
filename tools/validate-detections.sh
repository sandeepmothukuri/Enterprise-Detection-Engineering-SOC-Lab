#!/usr/bin/env bash
# Static/runtime validation for the detection layer.
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE=".env.example"

echo "[1/4] Compose syntax"
docker compose --env-file "$ENV_FILE" config --quiet
echo "PASS: docker-compose.yml"

echo "[2/4] Sigma YAML"
python3 - <<'PY'
from pathlib import Path
import yaml
files = sorted(Path("detection-rules/sigma").rglob("*.yml"))
if not files:
    raise SystemExit("FAIL: no Sigma rules found")
for path in files:
    data = yaml.safe_load(path.read_text())
    for key in ("title", "logsource", "detection"):
        if key not in data:
            raise SystemExit(f"FAIL: {path}: missing {key}")
print(f"PASS: {len(files)} Sigma rules parsed")
PY

echo "[3/4] Zeek compile"
docker run --rm \
  -v "$PWD/config/zeek:/opt/zeek/share/zeek/site:ro" \
  zeek/zeek:8.2.2 \
  zeek -C /opt/zeek/share/zeek/site/local.zeek >/tmp/soc-zeek-validation.log
grep -q "SOC Lab Zeek NSM started" /tmp/soc-zeek-validation.log
echo "PASS: Zeek 8 configuration compiles"

echo "[4/4] Suricata rule/config test"
docker run --rm \
  -e SURICATA_HOME_NET='[192.168.0.0/16,10.0.0.0/8,172.16.0.0/12]' \
  -v "$PWD/config/suricata/suricata.yaml:/etc/suricata/suricata.yaml:ro" \
  -v "$PWD/detection-rules/suricata:/etc/suricata/rules/custom:ro" \
  jasonish/suricata:7.0 \
  suricata -T -c /etc/suricata/suricata.yaml

echo "PASS: Suricata configuration and custom rules"
echo "All detection-layer validations passed."
