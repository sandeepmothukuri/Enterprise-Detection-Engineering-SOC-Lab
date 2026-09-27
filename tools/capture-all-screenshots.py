import os
import subprocess
import time
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboards" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_PATH):
    EDGE_PATH = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

PAGES = [
    ("00_portal", "index.html", "Security Operations Command Center Portal"),
    ("01_soc_command_center", "01_soc_command_center.html", "Tier 1: SOC Command Center"),
    ("02_incident_operations", "02_incident_operations.html", "Tier 2: Incident Operations & IRIS Cases"),
    ("03_detection_engineering", "03_detection_engineering.html", "Tier 3: Detection Engineering & Sigma"),
    ("04_mitre_attack", "04_mitre_attack.html", "Tier 4: MITRE ATT&CK Matrix & Scoring"),
    ("05_threat_hunting", "05_threat_hunting.html", "Tier 5: Threat Hunting Sandbox & VQL"),
    ("06_network_security", "06_network_security.html", "Tier 6: Network Security & NSM"),
    ("07_endpoint_security", "07_endpoint_security.html", "Tier 7: Endpoint Security & Process Trees"),
    ("08_ai_soc", "08_ai_soc.html", "Tier 8: Autonomous AI SOC & Multi-Agent Triage"),
    ("09_platform_health", "09_platform_health.html", "Tier 9: Platform Health & Reliability"),
    ("02_opensearch_siem", "02_opensearch_siem.html", "OpenSearch SIEM & Detection Engine"),
    ("03_zeek_network", "03_zeek_network.html", "Zeek NSM Network Connection & DNS Evidence"),
    ("04_suricata_ids", "04_suricata_ids.html", "Suricata 7.0 IDS/IPS & EVE Telemetry"),
    ("05_ai_agents", "05_ai_agents.html", "CrewAI Multi-Agent Autonomous SOC Engine"),
    ("06_iris_cases", "06_iris_cases.html", "DFIR-IRIS Incident Response & Case Management"),
    ("07_caldera_attack", "07_caldera_attack.html", "MITRE Caldera Adversary Emulation & Scoring"),
    ("08_misp_ti", "08_misp_ti.html", "MISP Threat Intelligence & Attribution Platform"),
    ("09_velociraptor", "09_velociraptor.html", "Velociraptor Live DFIR & VQL Artifact Engine"),
    ("10_responder_redteam", "10_responder_redteam.html", "Red Team Responder LLMNR/NBT-NS Poisoning"),
    ("12_purple_team", "12_purple_team.html", "Purple Team Matrix & SOAR Flowchart Visualizer"),
    ("14_cloud_security", "14_cloud_security.html", "Cloud SOC & Multi-Cloud Posture"),
    ("15_malware_analysis", "15_malware_analysis.html", "Malware Analysis & Memory Forensics Sandbox"),
    ("16_d3fend_matrix", "16_d3fend_matrix.html", "MITRE D3FEND Defensive Countermeasure Matrix"),
    ("17_asset_inventory", "17_asset_inventory.html", "Asset Inventory & EDR Health Radar"),
    ("18_threat_intel_feeds", "18_threat_intel_feeds.html", "Live Threat Intelligence Feed Hub"),
    ("19_network_topology", "19_network_topology.html", "Live SOC Network Topology & Flow Visualizer")
]

manifest = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "dashboard_count": len(PAGES),
    "theme": "darkblue",
    "captures": []
}

print(f"[*] Starting screenshot capture for {len(PAGES)} dashboards...")

for id_name, html_file, label in PAGES:
    out_file = OUT / f"{id_name}.png"
    url = f"http://localhost:8080/{html_file}"
    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1440,900",
        f"--screenshot={str(out_file)}",
        url
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        print(f"[+] Captured: {id_name}.png ({label})")
        manifest["captures"].append({
            "id": id_name,
            "filename": f"{id_name}.png",
            "label": label,
            "url": url,
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        print(f"[-] Failed {id_name}: {e}")

manifest_path = OUT / "capture_manifest.json"
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"\n[+] Screenshot capture complete. Manifest saved to {manifest_path}")
