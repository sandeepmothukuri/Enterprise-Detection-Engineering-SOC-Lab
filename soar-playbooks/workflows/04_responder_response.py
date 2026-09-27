#!/usr/bin/env python3
"""
SOAR Playbook #4: Responder / LLMNR Poisoning Response
MITRE ATT&CK: T1557.001
Steps:
  1. Identify source of poisoning
  2. Check if authorized red-team exercise (check Caldera operation)
  3. If NOT authorized: block + alert + investigate
  4. If authorized: log + continue monitoring
  5. Recommend disabling LLMNR via GPO
"""
import os
import requests
import json
try:
    from common import create_iris_case, log_soc_action, CALDERA_URL
except ImportError:
    from soar_playbooks.workflows.common import create_iris_case, log_soc_action, CALDERA_URL


def check_caldera_operation(ip: str) -> bool:
    """Check if this IP is a registered Caldera agent (authorized red team)."""
    try:
        r = requests.get(
            f"{CALDERA_URL}/api/v2/agents",
            headers={"KEY": os.getenv("CALDERA_API_KEY_BLUE", "")},
            timeout=5
        )
        if r.status_code == 200:
            agents = r.json()
            return any(a.get("paw", "") and ip in str(a) for a in agents)
        return False
    except Exception:
        return False


def run(alert: dict) -> dict:
    src_ip = alert.get("source_ip", "")
    iris_token = os.getenv("IRIS_TOKEN", "")
    print(f"[PLAYBOOK-04] Responder/LLMNR Response -> Source: {src_ip}")

    is_redteam = check_caldera_operation(src_ip)
    if is_redteam:
        print("  [+] Authorized red-team exercise detected — logging only")
        log_soc_action(
            action="redteam_exercise_observed",
            details={"ip": src_ip, "status": "authorized"},
            playbook_name="responder_response",
            mitre_technique="T1557.001"
        )
        return {"status": "authorized_exercise", "ip": src_ip}
    else:
        print(f"  [!] UNAUTHORIZED Responder activity from {src_ip}")
        case_id = create_iris_case(
            title=f"Unauthorized LLMNR/NBT-NS Poisoning from {src_ip}",
            description=f"Host {src_ip} detected broadcasting LLMNR/NBT-NS poison responses.",
            severity=3,
            token=iris_token
        )
        log_soc_action(
            action="quarantine_rogue_device",
            details={"ip": src_ip, "case_id": case_id},
            playbook_name="responder_response",
            mitre_technique="T1557.001"
        )
        print("  [+] Recommended: Disable LLMNR via GPO (Computer Config -> Admin Templates -> DNS Client)")
        return {
            "status": "unauthorized",
            "action": "block_and_alert",
            "case_id": case_id,
            "ip": src_ip,
            "remediation": "Disable LLMNR: GPO -> DNS Client -> Turn off Multicast Name Resolution"
        }


if __name__ == "__main__":
    sample = {"source_ip": "10.0.0.87", "mitre": "T1557.001"}
    print(json.dumps(run(sample), indent=2))
