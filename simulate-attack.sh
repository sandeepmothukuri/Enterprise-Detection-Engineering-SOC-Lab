#!/usr/bin/env bash
# Enterprise Detection Engineering SOC Lab — controlled training telemetry.
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT_DIR"

SCENARIO="${1:-apt29}"
[[ -f .env ]] || { echo "ERROR: .env is missing; run ./setup.sh first." >&2; exit 1; }
set -a
# shellcheck disable=SC1091
. ./.env
set +a

CA="config/opensearch/certs/root-ca.pem"
CERT="config/opensearch/certs/opensearch-admin.pem"
KEY="config/opensearch/certs/opensearch-admin-key.pem"
[[ -s "$CA" && -s "$CERT" && -s "$KEY" ]] || { echo "ERROR: OpenSearch TLS material is missing; run ./setup.sh." >&2; exit 1; }

OS_URL="https://127.0.0.1:${OPENSEARCH_PORT:-9200}"
INDEX="soc-logs-$(date -u +%Y.%m.%d)"

post_event() {
  local label="$1" technique="$2" tactic="$3" severity="$4" sensor="$5" description="$6"
  local payload
  payload=$(python3 - "$technique" "$tactic" "$severity" "$sensor" "$description" <<'PY'
import json, sys
from datetime import datetime, timezone
technique, tactic, severity, sensor, description = sys.argv[1:]
print(json.dumps({
    "@timestamp": datetime.now(timezone.utc).isoformat(),
    "event_type": "training_detection_test",
    "mitre_technique": technique,
    "mitre_tactic": tactic,
    "severity": severity,
    "sensor": sensor,
    "rule_name": technique.replace('.', '_'),
    "description": description,
}))
PY
)
  if curl -sS --fail --cacert "$CA" --cert "$CERT" --key "$KEY" \
      -X POST "$OS_URL/$INDEX/_doc" -H 'Content-Type: application/json' -d "$payload" >/dev/null; then
    echo "PASS: $label"
  else
    echo "FAIL: $label" >&2
    exit 1
  fi
}

run_apt29() {
  echo "APT-style controlled training scenario"
  post_event "T1566.001 spearphishing" T1566.001 initial-access high email-gateway "Suspicious attachment delivered to a finance workstation"
  post_event "T1059.001 PowerShell" T1059.001 execution high sysmon "Encoded PowerShell command executed"
  post_event "T1053.005 scheduled task" T1053.005 persistence medium sysmon "New scheduled task created for persistence"
  post_event "T1547.001 registry run key" T1547.001 persistence medium sysmon "Windows Run key modified"
  post_event "T1003.001 LSASS" T1003.001 credential-access critical sysmon "Suspicious process access to LSASS"
  post_event "T1110.001 password spray" T1110.001 credential-access high windows-security "Multiple failed logons across user accounts"
  post_event "T1557.001 LLMNR poisoning" T1557.001 credential-access high zeek "LLMNR response spoofing observed"
  post_event "T1021.002 SMB lateral movement" T1021.002 lateral-movement critical zeek "SMB connection to an administrative share"
  post_event "T1550.002 pass the hash" T1550.002 lateral-movement critical windows-security "NTLM logon consistent with pass-the-hash activity"
  post_event "T1046 network scan" T1046 discovery medium suricata "Port scan observed against an internal subnet"
  post_event "T1041 C2 exfiltration" T1041 exfiltration critical zeek "Large outbound transfer over a C2 channel"
  post_event "T1071.004 DNS tunneling" T1071.004 command-and-control high zeek "Long high-entropy DNS queries observed"
  post_event "T1562.001 Defender disable" T1562.001 defense-evasion critical sysmon "Windows Defender real-time monitoring disabled"
}

run_bruteforce() {
  echo "Brute-force/password-spray training scenario"
  local accounts=(jsmith mjohnson alee bwilliams cjones ddavis ewilson ftaylor gbrown hmartin ithompson jgarcia)
  for account in "${accounts[@]}"; do
    post_event "T1110.001 failed authentication for ${account}" T1110.001 credential-access medium windows-security "Failed authentication for ${account}"
  done
  post_event "T1110.001 account lockout" T1110.001 credential-access high windows-security "Account lockout threshold exceeded"
}

run_insider() {
  echo "Insider-threat training scenario"
  post_event "T1039 bulk file collection" T1039 collection medium file-audit "Large number of files accessed from a network share"
  post_event "T1560.001 archive staging" T1560.001 collection high sysmon "Large archive created from collected files"
  post_event "T1052.001 removable media" T1052.001 exfiltration high windows-security "Removable storage device connected"
  post_event "T1567.002 cloud upload" T1567.002 exfiltration critical proxy "Large upload to cloud storage"
  post_event "T1078 after-hours login" T1078 defense-evasion medium windows-security "Interactive account login outside the normal working schedule"
  post_event "T1114.003 email forwarding" T1114.003 collection high o365-audit "Mailbox forwarding rule created"
  post_event "T1133 external remote service" T1133 initial-access high vpn-gateway "VPN login from an unusual geography"
  post_event "T1213 data from information repositories" T1213 collection critical db-audit "Large sensitive database query"
  post_event "T1070.004 file deletion" T1070.004 defense-evasion critical sysmon "Evidence and event-log deletion activity observed"
}

run_verify() {
  echo "Verifying generated training telemetry"
  total=$(curl -sS --fail --cacert "$CA" --cert "$CERT" --key "$KEY" \
    "$OS_URL/$INDEX/_count" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("count",0))')
  echo "Documents in $INDEX: $total"
  [[ "$total" =~ ^[0-9]+$ ]] || exit 1
  (( total > 0 )) || { echo "No training telemetry found." >&2; exit 1; }
}

case "$SCENARIO" in
  apt29) run_apt29 ;;
  bruteforce) run_bruteforce ;;
  insider) run_insider ;;
  verify) run_verify ;;
  all) run_apt29; run_bruteforce; run_insider; run_verify ;;
  *) echo "Usage: $0 [apt29|bruteforce|insider|verify|all]" >&2; exit 1 ;;
esac
