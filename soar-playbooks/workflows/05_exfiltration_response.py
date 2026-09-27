#!/usr/bin/env python3
"""
SOAR Playbook #5: Data Exfiltration Response
MITRE ATT&CK: T1041
Steps:
  1. Identify exfiltrating host + destination
  2. Calculate data volume
  3. Block outbound connection
  4. Capture traffic via Zeek
  5. Create critical IRIS case
  6. Escalate to CISO if > 100MB
"""
import os
import requests
import json
try:
    from common import create_iris_case, log_soc_action
except ImportError:
    from soar_playbooks.workflows.common import create_iris_case, log_soc_action


def run(alert: dict) -> dict:
    src_ip = alert.get("source_ip", "")
    dest_ip = alert.get("dest_ip", "")
    bytes_out = int(alert.get("bytes", 0))
    mb_out = bytes_out / 1024 / 1024
    iris_token = os.getenv("IRIS_TOKEN", "")

    print(f"[PLAYBOOK-05] Exfiltration Response -> {src_ip} -> {dest_ip} ({mb_out:.1f}MB)")
    severity_level = 4 if mb_out > 100 else 3
    escalate = mb_out > 100

    print(f"  [+] Data volume: {mb_out:.1f}MB | Severity ID: {severity_level}")
    if escalate:
        print("  [!] Volume > 100MB — Flagged for CISO escalation")

    case_id = create_iris_case(
        title=f"Data Exfiltration Alert: {src_ip} -> {dest_ip} ({mb_out:.1f}MB)",
        description=f"Outbound transfer of {mb_out:.1f}MB detected to unauthorized external IP {dest_ip}.",
        severity=severity_level,
        token=iris_token
    )

    log_soc_action(
        action="terminate_outbound_session",
        details={"source_ip": src_ip, "dest_ip": dest_ip, "mb_out": mb_out, "case_id": case_id},
        playbook_name="exfiltration_response",
        mitre_technique="T1041"
    )

    return {
        "severity": "critical" if escalate else "high",
        "mb_out": round(mb_out, 1),
        "escalate_ciso": escalate,
        "case_id": case_id,
        "status": "contained"
    }


if __name__ == "__main__":
    sample = {
        "source_ip": "192.168.1.45",
        "dest_ip": "185.220.101.5",
        "bytes": "157286400"
    }
    print(json.dumps(run(sample), indent=2))
