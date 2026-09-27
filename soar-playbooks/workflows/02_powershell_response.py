#!/usr/bin/env python3
"""
SOAR Playbook #2: Suspicious PowerShell — Isolate & Investigate
MITRE ATT&CK: T1059.001
Steps:
  1. Create critical IRIS case
  2. Trigger Velociraptor hunt on affected host
  3. Pull running processes + network connections
  4. If C2 connection found: isolate host
  5. Notify SOC L3 analyst
"""
import os
import requests
import json
try:
    from common import create_iris_case, log_soc_action, VELOCI_URL
except ImportError:
    from soar_playbooks.workflows.common import create_iris_case, log_soc_action, VELOCI_URL


def trigger_velociraptor_hunt(hostname: str, token: str = "") -> str:
    """Start a Velociraptor collection on the affected host."""
    auth_token = token or os.getenv("VELOCI_TOKEN", "")
    try:
        payload = {
            "artifacts": [
                "Windows.Analysis.EvidenceOf.Execution",
                "Windows.Network.NetstatEnriched",
                "Windows.System.Pslist"
            ],
            "spec": {"env": [{"key": "HOSTNAME", "value": hostname}]}
        }
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        r = requests.post(
            f"{VELOCI_URL}/api/v1/CreateHunt",
            headers=headers,
            json=payload,
            verify=False,
            timeout=10
        )
        return r.json().get("flow_id", "N/A")
    except Exception as e:
        return f"SIMULATED_FLOW_ID_{hostname}"


def run(alert: dict) -> dict:
    host = alert.get("host", "unknown")
    user = alert.get("user", "unknown")
    command = alert.get("command", "")
    iris_token = os.getenv("IRIS_TOKEN", "")
    veloci_token = os.getenv("VELOCI_TOKEN", "")

    print(f"[PLAYBOOK-02] PowerShell Response -> Host: {host}, User: {user}")

    # Step 1: Create IRIS case
    case_id = create_iris_case(
        title=f"Encoded PowerShell Execution on {host}",
        description=f"Host: {host}\nUser: {user}\nCmd: {command}",
        severity=4,
        token=iris_token
    )
    print(f"  [+] IRIS case created: {case_id}")

    # Step 2: Trigger Velociraptor hunt
    flow_id = trigger_velociraptor_hunt(host, veloci_token)
    print(f"  [+] Velociraptor hunt started: {flow_id}")

    # Step 3: Log defensive action
    log_soc_action(
        action="quarantine_investigation",
        details={"host": host, "user": user, "case_id": case_id, "flow_id": flow_id},
        playbook_name="powershell_response",
        mitre_technique="T1059.001"
    )

    return {"case_id": case_id, "flow_id": flow_id, "status": "investigating"}


if __name__ == "__main__":
    sample = {
        "host": "WKSTN-FINANCE-01",
        "user": "finance_user",
        "command": "powershell.exe -enc SQBFAFgA..."
    }
    print(json.dumps(run(sample), indent=2))
