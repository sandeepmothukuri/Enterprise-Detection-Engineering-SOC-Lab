# Enterprise Detection Engineering SOC Lab

[![CI](https://github.com/sandeepmothukuri/Enterprise-Detection-Engineering-SOC-Lab/actions/workflows/soc-lab-ci.yml/badge.svg)](https://github.com/sandeepmothukuri/Enterprise-Detection-Engineering-SOC-Lab/actions) [![Website](https://img.shields.io/badge/Website-cybertechnology.in-blue)](https://cybertechnology.in) [![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK-red)](https://attack.mitre.org/)

> A hands-on, open-source Security Operations Center lab running a production-style detection, network monitoring, threat intelligence, DFIR, SOAR, adversary-emulation and AI-assisted workflow through Docker Compose.

**Author:** Sandeep Mothukuri  
**Stack:** OpenSearch · Vector · Zeek · Suricata · ElastAlert2 · MISP · DFIR-IRIS · Velociraptor · StackStorm · MITRE Caldera · Responder · Ollama/CrewAI  
**Target:** SOC Level 2/3 analysts · Detection Engineers · Threat Hunters · Incident Responders  
**Minimum:** 16 GB RAM · 50 GB disk · Linux / WSL2 / macOS

---

## What This Lab Demonstrates

This repository models an end-to-end SOC workflow rather than a collection of disconnected security tools:

```text
Adversary Emulation
       │
       ▼
Network / Host Telemetry
       │
       ├── Zeek
       └── Suricata
       │
       ▼
Log Routing / Normalisation
       │
       └── Vector
       │
       ▼
Detection & SIEM
       │
       ├── OpenSearch
       └── ElastAlert2
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
Threat Intel      Case Mgmt       DFIR
   MISP           DFIR-IRIS    Velociraptor
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                SOAR / Response
                  StackStorm
                      │
                      ▼
               AI-Assisted Analysis
                 Ollama + CrewAI
```

The objective is to demonstrate how telemetry becomes detections, detections become investigations, and investigations drive response and threat-hunting actions.

---

## Evidence & Screenshots

The screenshots below are repository evidence views. Native-tool screenshots are captured from the running lab with `tools/capture-live-screenshots.py`; local dashboard screenshots are captured from the repository's own evidence views.

> **Evidence policy:** Screenshots must come from the running lab or from the repository's actual dashboard pages. No AI-generated or fabricated SOC screenshots are used as operational evidence.

### 01 — Command Center Portal

The entry point for the lab and its operational services.

![SOC Lab Portal](dashboards/screenshots/00_portal.png)

### 02 — SOC Overview

Consolidated analyst view for alerts, severity, activity and investigation workflow.

![SOC Overview](dashboards/screenshots/01_soc_overview.png)

### 03 — OpenSearch SIEM

Native OpenSearch Dashboards evidence for indexed security telemetry and SIEM investigation.

![OpenSearch SIEM](dashboards/screenshots/02_opensearch_siem.png)

### 04 — Zeek Network Security Monitoring

Network telemetry and protocol-level visibility used for detection engineering and hunting.

![Zeek Network](dashboards/screenshots/03_zeek_network.png)

### 05 — Suricata IDS

IDS telemetry and EVE JSON alert evidence for network detections.

![Suricata IDS](dashboards/screenshots/04_suricata_ids.png)

### 06 — AI-Assisted SOC Analysis

CrewAI/Ollama workflow for analyst-assisted triage, threat analysis, hunting and detection engineering.

![AI Agents](dashboards/screenshots/05_ai_agents.png)

### 07 — DFIR-IRIS Case Management

Incident case management and investigation workflow for turning detections into trackable incidents.

![DFIR-IRIS](dashboards/screenshots/06_iris_cases.png)

### 08 — MITRE Caldera Adversary Emulation

Controlled adversary-emulation activity mapped to MITRE ATT&CK techniques.

![Caldera](dashboards/screenshots/07_caldera_attack.png)

### 09 — MISP Threat Intelligence

IOC and threat-intelligence workflow supporting enrichment, correlation and investigation.

![MISP](dashboards/screenshots/08_misp_ti.png)

### 10 — Velociraptor DFIR

Endpoint visibility and VQL-based forensic investigation capabilities.

![Velociraptor](dashboards/screenshots/09_velociraptor.png)

### 11 — Red Team / Responder

Isolated lab evidence for Responder and LLMNR/NBT-NS poisoning scenarios.

![Red Team](dashboards/screenshots/10_responder_redteam.png)

### Screenshot Provenance

Live screenshot capture is intentionally separated from image generation. Run the lab first, generate telemetry, then capture the interfaces:

```bash
sudo ./setup.sh
./health-check.sh
./simulate-attack.sh apt29
./tools/capture-live-screenshots.sh
```

For selected native services:

```bash
./tools/capture-live-screenshots.sh --only 02_opensearch_siem,07_caldera_attack,08_misp_ti
```

For a visible browser session:

```bash
./tools/capture-live-screenshots.sh --headed
```

The capture utility writes `dashboards/screenshots/capture-manifest.json`, recording the capture timestamp, source type, URL, reachability and result. See [`docs/LIVE_SCREENSHOT_CAPTURE.md`](docs/LIVE_SCREENSHOT_CAPTURE.md) for the evidence workflow.

---

## Overview

The lab is a self-contained security operations environment designed for hands-on detection engineering, threat hunting, incident response, DFIR, SOAR and adversary-emulation practice. Components are orchestrated with Docker Compose and can be deployed on a single sufficiently sized workstation.

### Tooling Matrix

| Layer | Tool | Purpose |
|---|---|---|
| **SIEM** | OpenSearch 2.13 + Dashboards | Log ingestion, search and visualization |
| **Log Pipeline** | Vector 0.38 | Unified log routing and transformation |
| **Detection** | ElastAlert2 | Rule-based alerting from OpenSearch |
| **Network NSM** | Zeek 6.0 + Suricata 7.0 | Network security monitoring and IDS |
| **SOAR** | StackStorm 3.8 | Automated response playbooks |
| **Case Management** | DFIR-IRIS 2.4 | Incident tracking, timelines and IOCs |
| **Threat Intelligence** | MISP | IOC management and threat intelligence |
| **DFIR** | Velociraptor | Live forensics and VQL hunting |
| **Attack Simulation** | MITRE Caldera 5.x | Adversary emulation and ATT&CK mapping |
| **Red Team** | Responder | LLMNR/NBT-NS poisoning in an isolated lab |
| **AI Analysis** | Ollama + CrewAI | LLM-assisted SOC analysis |

### Detection Rules

The repository includes 15 built-in detection scenarios mapped to MITRE ATT&CK:

| Rule | Technique | Severity |
|---|---|---|
| Brute Force / Password Spray | T1110.001 | High |
| LSASS Memory Dump | T1003.001 | Critical |
| PowerShell Encoded Command | T1059.001 | High |
| Lateral Movement via SMB | T1021.002 | Critical |
| LLMNR/NBT-NS Poisoning | T1557.001 | High |
| Scheduled Task Creation | T1053.005 | Medium |
| Registry Run Key Persistence | T1547.001 | Medium |
| DNS Tunneling C2 | T1071.004 | High |
| Pass-the-Hash | T1550.002 | Critical |
| Network Port Scan | T1046 | Medium |
| Data Exfiltration over C2 | T1041 | Critical |
| Defender Disabled | T1562.001 | Critical |
| Spearphishing Attachment | T1566.001 | High |
| Bulk File Collection | T1039 | Medium |
| After-Hours Account Login | T1078 | Medium |

### AI Agents

| Agent | Role | Capability |
|---|---|---|
| Threat Analyst | APT attribution, TTP mapping | Correlates IOCs with threat actors |
| Incident Responder | Triage and containment | Generates response playbooks |
| Threat Hunter | Proactive hunting | Builds VQL queries from hypotheses |
| Detection Engineer | Rule creation | Writes ElastAlert2 and Sigma rules |

---

## Architecture

```text
Internet / Lab Network
        │
   ┌────▼─────────────────────────────────────────────┐
   │              Docker Compose Network               │
   │                                                   │
   │  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
   │  │  Zeek    │  │ Suricata │  │  Log Sources   │  │
   │  │ (NSM)    │  │ (IDS)    │  │  Sysmon/Win    │  │
   │  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
   │       └─────────────┴────────────────┘           │
   │                     │ Vector 0.38                 │
   │               ┌─────▼──────┐                      │
   │               │ OpenSearch │◄─── ElastAlert2      │
   │               │  (SIEM)    │                      │
   │               └─────┬──────┘                      │
   │                     │                             │
   │        ┌────────────┼────────────┐                │
   │        ▼            ▼            ▼                │
   │   StackStorm    DFIR-IRIS      MISP               │
   │   (SOAR)       (Cases)        (Threat Intel)      │
   │        │            │            │                │
   │        └────────────┴────────────┘                │
   │                     │                             │
   │              ┌──────▼──────┐                      │
   │              │  AI Agents  │                      │
   │              │ Ollama/Crew │                      │
   │              └─────────────┘                      │
   │                                                   │
   │  ┌──────────────┐   ┌──────────────┐              │
   │  │    Caldera   │   │  Velociraptor│              │
   │  │  (Attack Sim)│   │    (DFIR)    │              │
   │  └──────────────┘   └──────────────┘              │
   └───────────────────────────────────────────────────┘
```

---

## Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| RAM | 16 GB | 16–32 GB |
| Disk | 50 GB | 50+ GB |
| CPU | 4 cores | 8 cores |
| OS | Ubuntu 22.04 / Debian 12 / WSL2 / macOS | Ubuntu 22.04 LTS |
| Docker | 24.x | Latest |
| Docker Compose | v2.x | Latest |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/sandeepmothukuri/Enterprise-Detection-Engineering-SOC-Lab.git
cd Enterprise-Detection-Engineering-SOC-Lab
```

### 2. Make Scripts Executable

```bash
chmod +x setup.sh health-check.sh simulate-attack.sh tools/capture-live-screenshots.sh
```

### 3. Run the Setup Script

The setup script handles environment configuration, kernel tuning, Docker image pulls and staged service deployment.

```bash
sudo ./setup.sh
```

The deployment is staged as:

```text
Stage 1/4 — Core infrastructure (OpenSearch, Vector)
Stage 2/4 — Security tools (MISP, IRIS, Velociraptor)
Stage 3/4 — SOAR + Detection (StackStorm, ElastAlert2)
Stage 4/4 — AI agents + Attack simulation (Ollama, Caldera)
```

> **First run:** Ollama downloads the configured model and may require several GB of additional disk space. Setup time depends on CPU, storage and network speed.

### 4. Verify Services

```bash
./health-check.sh
```

---

## Configuration

Credentials are generated by `setup.sh` into `.env`. Review the generated configuration before using the environment.

```bash
cat .env
```

> **Security:** Do not expose the lab directly to the internet. Change default credentials and keep attack-simulation/red-team components on an isolated network.

---

## Running Attack Simulations

The `simulate-attack.sh` utility injects controlled MITRE ATT&CK-style events into OpenSearch for analyst training and detection validation.

```bash
./simulate-attack.sh apt29
./simulate-attack.sh bruteforce
./simulate-attack.sh insider
./simulate-attack.sh all
```

After generating telemetry, validate the detection path and capture evidence:

```bash
./health-check.sh
./tools/capture-live-screenshots.sh
```

---

## Service Endpoints

When the stack is running locally, the principal interfaces are:

| Service | Local endpoint |
|---|---|
| OpenSearch API | `http://127.0.0.1:9200` |
| OpenSearch Dashboards | `http://127.0.0.1:5601` |
| DFIR-IRIS | `https://127.0.0.1:8443` |
| MISP | `http://127.0.0.1:8080` |
| Velociraptor | `https://127.0.0.1:8889` |
| MITRE Caldera | `http://127.0.0.1:8888` |
| StackStorm | `http://127.0.0.1:9101` |
| AI Agents API | `http://127.0.0.1:8500` |
| Ollama | `http://127.0.0.1:11434` |

> ⚠️ These endpoints are intended for a local lab. Do not expose them publicly with default credentials.

---

## Optional: Red Team Profile

Responder is disabled by default and should only be used on an isolated lab network.

```bash
docker compose --profile redteam up -d
docker compose --profile redteam down
```

---

## Live Screenshot Capture

The repository includes a reproducible Playwright capture workflow for collecting evidence from the running lab without fabricating UI data.

```bash
./tools/capture-live-screenshots.sh
```

Useful options:

```bash
./tools/capture-live-screenshots.sh --headed
./tools/capture-live-screenshots.sh --strict
./tools/capture-live-screenshots.sh --only 02_opensearch_siem,06_iris_cases,07_caldera_attack,08_misp_ti,09_velociraptor
```

See [`docs/LIVE_SCREENSHOT_CAPTURE.md`](docs/LIVE_SCREENSHOT_CAPTURE.md) for the capture matrix, prerequisites and provenance manifest.

---

## Project Structure

```text
.
├── dashboards/                    # SOC dashboards and screenshot evidence
│   └── screenshots/               # Captured evidence images + manifest
├── detections/                    # Detection rules and mappings
├── configs/                       # Service configuration
├── docs/                          # Architecture and operational documentation
├── tools/                         # Health checks and evidence automation
├── docker-compose.yml             # Lab orchestration
├── setup.sh                       # Staged environment setup
├── health-check.sh                # Service health validation
└── simulate-attack.sh             # Controlled attack telemetry generation
```

---

## Author

### Sandeep Mothukuri

**Senior SOC Analyst (L3) · Detection Engineering · Threat Hunting · Incident Response · Security Engineering**

Focus areas:

- Security Operations
- Detection Engineering
- Threat Hunting
- Incident Response
- SIEM / XDR
- SOAR
- DFIR
- MITRE ATT&CK
- Security Automation
- AI-Augmented SOC Operations

This repository is maintained as a practical security engineering environment for designing, testing and validating modern SOC capabilities.

- GitHub: [@sandeepmothukuri](https://github.com/sandeepmothukuri)
- Website: [cybertechnology.in](https://cybertechnology.in)
- LinkedIn: [linkedin.com/in/sandeepmothukuri](https://www.linkedin.com/in/sandeepmothukuri)
- Email: [sandeep.mothukuris@gmail.com](mailto:sandeep.mothukuris@gmail.com)

---

## Related Repositories

| Repository | Description |
|---|---|
| [AI-SOC-Decision-Engine](https://github.com/sandeepmothukuri/AI-SOC-Decision-Engine) | AI-assisted SOC decision/control plane for triage, enrichment, safety controls and analyst approval |
| [AI-Augmented-SOC-Lab](https://github.com/sandeepmothukuri/AI-Augmented-SOC-Lab) | AI-augmented SOC with Wazuh, TheHive and Ollama for analyst-assisted triage |
| [Enterprise-Detection-Engineering-SOC-Lab](https://github.com/sandeepmothukuri/Enterprise-Detection-Engineering-SOC-Lab) | Detection engineering SOC lab with OpenSearch, Suricata, Zeek, MISP, Caldera and Velociraptor |
| [Autonomous-SOC-Lab](https://github.com/sandeepmothukuri/Autonomous-SOC-Lab) | Autonomous SOC with AI-driven detection and response workflows |
| [soc-threat-hunting-lab](https://github.com/sandeepmothukuri/soc-threat-hunting-lab) | Threat hunting lab using Zeek, RITA, Arkime, Velociraptor, OSQuery and MISP |
| [soc-lab-free](https://github.com/sandeepmothukuri/soc-lab-free) | Free SOC lab covering vulnerability management, Wazuh, pfSense, email security and Linux hardening |
| [SOC-Detection-and-Threat-Hunting-Lab](https://github.com/sandeepmothukuri/SOC-Detection-and-Threat-Hunting-Lab) | SOC analyst home lab with Wazuh, Sysmon, MITRE ATT&CK mapping and incident response |
| [PromptSentinel](https://github.com/sandeepmothukuri/PromptSentinel) | Prompt injection detection and AI firewall for LLM applications |
| [PromptShield](https://github.com/sandeepmothukuri/PromptShield) | AI security and SOC detection engineering lab with prompt-security telemetry and response |
| [sentinel-detection-engine](https://github.com/sandeepmothukuri/sentinel-detection-engine) | Detection-as-code for Microsoft Sentinel and Defender XDR with KQL, SOAR and ATT&CK coverage |

---

## License

MIT License. See [`LICENSE`](LICENSE).

**Author portfolio:** [github.com/sandeepmothukuri](https://github.com/sandeepmothukuri)
