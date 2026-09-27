# OpenSearch Telemetry Data Model & Field Specification

Author: Sandeep Mothukuri ([@sandeepmothukuri](https://github.com/sandeepmothukuri))  
Platform: Enterprise Detection Engineering & SOC Operations Lab v2

---

## 1. Overview & Data Philosophy

This document defines the production data schema, index naming conventions, field mappings, and telemetry normalization applied across the **Enterprise Detection Engineering & SOC Operations Platform**.

### Core Tenet: Signal > Decoration
- **No Fabricated Telemetry**: Every dashboard panel, visual metric, and alerting rule binds to strictly validated OpenSearch indices and normalized fields.
- **Explicit Missing Metric Disclosure**: In enterprise environments without bidirectional ITSM integration (e.g., ServiceNow/Jira Service Desk), true Mean Time to Remediate (MTTR) cannot be calculated without recording verified `incident.closed_at` timestamps across all raw log events. In this platform, rather than inventing false MTTR values, we provide measurable operational metrics: **Alert Volume by Severity**, **Detection Hits per Tactic**, **Active Incident Queue State**, and **Rule Trigger Frequency**.

---

## 2. OpenSearch Index Patterns & Lifecycle

| Index Pattern | Source Engine | Purpose | Retention |
| :--- | :--- | :--- | :--- |
| `soc-logs-*` | Vector Ingestion Pipeline | Normalized raw telemetry (Sysmon, Zeek, Suricata, Auditd, Auth) | 30 Days |
| `soc-alerts-*` | ElastAlert2 / Sigma Engine | Actionable detection rule triggers, severity scoring, MITRE tags | 90 Days |
| `soc-ai-*` | CrewAI Autonomous Agents | Multi-agent triage verdicts, confidence scores, incident summaries | 90 Days |
| `soc-health-*` | Vector Internal Metrics & Docker | Pipeline throughput (EPS), container health, indexing latency | 14 Days |

---

## 3. Unified Field Normalization Schema (`soc-logs-*`)

| Field Name | Type | Source Sensors | Description / Example Values |
| :--- | :--- | :--- | :--- |
| `@timestamp` | `date` | All Sensors | ISO 8601 UTC timestamp of log generation |
| `sensor` | `keyword` | Sysmon, Zeek, Suricata, Auditd | Sensor telemetry source identifier (`sysmon`, `zeek`, `suricata`, `auditd`) |
| `severity` | `keyword` | ElastAlert2 / Normalizer | Normalized severity rating: `critical`, `high`, `medium`, `low`, `info` |
| `host.name` | `keyword` | Sysmon, Auditd, Beats | Hostname of the endpoint (`WIN-DC01`, `SRV-APP01`, `WS-SEC-09`) |
| `host.ip` | `ip` | Network / Endpoints | Primary IPv4 address of the endpoint (`10.0.0.15`, `172.20.0.10`) |
| `user.name` | `keyword` | Windows Security, Sysmon | Subject username associated with event (`SYSTEM`, `Administrator`, `jdoe`) |
| `src_ip` | `ip` | Zeek, Suricata, Sysmon | Source IP address initiating network connection or event |
| `dst_ip` | `ip` | Zeek, Suricata, Sysmon | Destination IP address receiving network connection or event |
| `src_port` | `integer` | Zeek, Suricata, Sysmon | Source transport layer port (`49152`, `5353`) |
| `dst_port` | `integer` | Zeek, Suricata, Sysmon | Destination transport layer port (`445`, `80`, `443`, `88`, `53`) |
| `proto` | `keyword` | Zeek, Suricata | Protocol identifier (`tcp`, `udp`, `icmp`) |
| `service` | `keyword` | Zeek | Application layer protocol detected (`dns`, `http`, `ssl`, `smb`, `dce_rpc`) |
| `EventID` | `integer` | Sysmon, Windows Events | Windows Event ID (`1`=Process Create, `8`=CreateRemoteThread, `10`=ProcessAccess, `11`=FileCreate) |
| `Image` | `keyword` | Sysmon | Fully qualified path to executed binary (`C:\Windows\System32\cmd.exe`) |
| `CommandLine` | `text` | Sysmon, Auditd | Full command line string executed with arguments |
| `ParentImage` | `keyword` | Sysmon | Binary path of parent process (`C:\Windows\explorer.exe`) |
| `ParentCommandLine`| `text` | Sysmon | Full command line arguments of parent process |
| `TargetImage` | `keyword` | Sysmon (EventID 10) | Target binary for process access / LSASS inspection |
| `GrantedAccess` | `keyword` | Sysmon (EventID 10) | Hexadecimal access mask requested (`0x1010`, `0x1FFFFF`) |
| `rule_name` | `keyword` | Sigma / ElastAlert2 | Human-readable detection rule name (`LSASS Memory Dump`, `Encoded PowerShell`) |
| `rule_id` | `keyword` | Sigma | Unique detection rule identifier (`SIG-WIN-001`, `SIG-NET-002`) |
| `mitre_tactic` | `keyword` | Sigma / Vector Enrichment | MITRE ATT&CK tactic category (`credential-access`, `lateral-movement`) |
| `mitre_technique` | `keyword` | Sigma / Vector Enrichment | MITRE ATT&CK technique identifier (`T1003.001`, `T1059.001`, `T1021.002`) |
| `dns.query` | `keyword` | Zeek (dns.log), Sysmon (EventID 22) | Fully qualified domain name queried (`c2.evil-attacker.org`, `wpad.local`) |
| `dns.rcode` | `keyword` | Zeek | DNS response code (`NOERROR`, `NXDOMAIN`, `SERVFAIL`) |
| `http.status_code` | `integer` | Zeek (http.log) | HTTP response code returned (`200`, `404`, `500`) |
| `tls.server_name` | `keyword` | Zeek (ssl.log) | TLS SNI hostname indicated during handshake |
| `alert.signature` | `keyword` | Suricata | Suricata IDS signature text (`ET MALWARE Suspicious DNS Beacon`) |

---

## 4. Multi-Agent AI Telemetry Schema (`soc-ai-*`)

| Field Name | Type | Description / Example Values |
| :--- | :--- | :--- |
| `agent_name` | `keyword` | Name of the CrewAI agent (`TriageAnalyst`, `ThreatHunter`, `EscalationLead`) |
| `verdict` | `keyword` | Classification output: `true_positive`, `false_positive`, `benign_test`, `needs_escalation` |
| `confidence` | `float` | AI classification confidence score (Range: `0.00` to `1.00`, e.g. `0.94`) |
| `reasoning` | `text` | Natural language explanation generated by local LLM based on artifacts |
| `recommended_action` | `text` | Action recommendation: `Isolate Host`, `Revoke Kerberos Ticket`, `Block IP at Firewall` |
| `human_reviewed` | `boolean` | Flag indicating whether tier-3 analyst verified the AI output |

---

## 5. Platform Health & Ingestion Metrics (`soc-health-*`)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `component` | `keyword` | Monitored microservice (`vector-aggregator`, `opensearch-node1`, `suricata-ids`, `zeek-nsm`) |
| `status` | `keyword` | Health state (`healthy`, `degraded`, `stopped`) |
| `events_per_second`| `float` | Real-time events processed per second |
| `buffer_utilization`| `float` | Percentage of disk/memory buffer currently utilized |
| `dropped_events` | `integer` | Cumulative count of unparsable or dropped events |
