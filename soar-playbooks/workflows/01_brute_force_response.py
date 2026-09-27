#!/usr/bin/env python3
"""
SOAR Playbook #1: Brute Force Auto-Response
MITRE ATT&CK: T1110
Trigger: ElastAlert2 → StackStorm webhook
Steps:
  1. Enrich source IP (MISP)
  2. Threat Scoring (0-10)
  3. IF score >= 7: log block action to OpenSearch + create IRIS case + notify
  4. ELSE: add to watchlist + alert analyst
"""
import os
import json
from datetime import datetime, timezone
try:
    from common import enrich_ip_misp, create_iris_case, log_soc_action
except ImportError:
    from soar_playbooks.workflows.common import enrich_ip_misp, create_iris_case, log_soc_action


def run(alert: dict) -> dict:
    src_ip = alert.get("source_ip", "unknown")
    fail_cnt = int(alert.get("count", 0))
    misp_key = os.getenv("MISP_KEY", "")
    iris_token = os.getenv("IRIS_TOKEN", "")

    print(f"[PLAYBOOK-01] Brute Force Response -> IP: {src_ip}, Failures: {fail_cnt}")

    # Step 1: MISP enrichment
    intel = enrich_ip_misp(src_ip, misp_key)
    print(f"  MISP hits: {intel.get('hits', 0)}")

    # Step 2: Calculate threat score
    score = 0
    if intel.get("hits", 0) > 0:
        score += 5
    if intel.get("hits", 0) > 5:
        score += 2
    if fail_cnt > 50:
        score += 2
    if fail_cnt > 200:
        score += 1
    print(f"  Threat score: {score}/10")

    # Step 3: Decision tree
    if score >= 7:
        log_soc_action(
            action="block_ip",
            details={"ip": src_ip, "failures": fail_cnt, "score": score},
            playbook_name="brute_force_response",
            mitre_technique="T1110"
        )
        case_id = create_iris_case(
            title=f"Brute Force Attack from {src_ip}",
            description=f"IP {src_ip} performed {fail_cnt} failed auth attempts.\nMISP hits: {intel.get('hits', 0)}\nScore: {score}/10",
            severity=3,
            token=iris_token
        )
        print(f"  [+] IP blocked | IRIS case: {case_id}")
        return {"action": "blocked", "case_id": case_id, "score": score}
    else:
        print(f"  [!] Score {score} < 7 — adding to watchlist")
        return {"action": "watchlist", "score": score}


if __name__ == "__main__":
    sample = {"source_ip": "10.0.0.87", "count": "241", "mitre": "T1110"}
    print(json.dumps(run(sample), indent=2))
