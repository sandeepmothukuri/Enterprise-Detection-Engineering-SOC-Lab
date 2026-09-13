# Enterprise Detection Engineering SOC Lab

[![CI](https://github.com/sandeepmothukuri/Enterprise-Detection-Engineering-SOC-Lab/actions/workflows/soc-lab-ci.yml/badge.svg)](https://github.com/sandeepmothukuri/Enterprise-Detection-Engineering-SOC-Lab/actions) [![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK-red)](https://attack.mitre.org/) [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> A hands-on, open-source Security Operations Center engineering lab for detection engineering, threat hunting, incident response, DFIR, threat intelligence, SOAR, adversary emulation and AI-assisted analysis.

**Author:** Sandeep Mothukuri  
**Stack:** OpenSearch · Vector · Zeek · Suricata · ElastAlert2 · MISP · DFIR-IRIS · Velociraptor · StackStorm · MITRE Caldera · Responder · Ollama/CrewAI  
**Target:** SOC Level 2/3 Analysts · Detection Engineers · Threat Hunters · Incident Responders  
**Deployment:** Docker Compose · Local / isolated lab  
**Minimum:** 16 GB RAM · 50 GB disk · Linux / WSL2 / macOS

---

## Table of Contents

- [Project Overview](#project-overview)
- [What This Lab Demonstrates](#what-this-lab-demonstrates)
- [Engineering Objectives](#engineering-objectives)
- [End-to-End SOC Workflow](#end-to-end-soc-workflow)
- [Architecture](#architecture)
- [Tooling](#tooling)
- [Detection Engineering](#detection-engineering)
- [MITRE ATT&CK Coverage](#mitre-attck-coverage)
- [Threat Hunting](#threat-hunting)
- [Incident Response & DFIR](#incident-response--dfir)
- [Threat Intelligence](#threat-intelligence)
- [Adversary Emulation](#adversary-emulation)
- [SOAR & Automation](#soar--automation)
- [AI-Assisted SOC](#ai-assisted-soc)
- [Detection Validation](#detection-validation)
- [Evidence & Screenshots](#evidence--screenshots)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Attack Simulation](#attack-simulation)
- [Service Endpoints](#service-endpoints)
- [Live Screenshot Capture](#live-screenshot-capture)
- [Project Structure](#project-structure)
- [Security & Lab Safety](#security--lab-safety)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Documentation](#documentation)
- [Author](#author)
- [License](#license)

---

## Project Overview

This project is designed as a **practical SOC engineering environment**, not a collection of unrelated Docker containers. The objective is to reproduce the major stages an analyst or detection engineer works through during a security investigation:

1. Generate or observe security telemetry.
2. Route and normalise the telemetry.
3. Search and correlate events in a SIEM.
4. Apply detection logic and ATT&CK mappings.
5. Enrich suspicious activity with threat intelligence.
6. Open and track an investigation.
7. Perform endpoint/network investigation and hunting.
8. Trigger response automation where appropriate.
9. Use AI as analyst assistance rather than an autonomous authority.
10. Validate whether the detection actually worked and improve it.

The repository therefore combines **engineering artifacts**—rules, configurations, scripts and orchestration—with **operational evidence** such as dashboards and screenshots.

### Core design principle

> **Attack → Telemetry → Detection → Triage → Enrichment → Investigation → Response → Validation → Detection Improvement**

That feedback loop is the main purpose of the lab.

---

## What This Lab Demonstrates

```text
                         ┌─────────────────────┐
                         │ Adversary Emulation  │
                         │ MITRE Caldera       │
                         │ Responder (optional) │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │ Security Telemetry           │
                    │ Zeek · Suricata · host logs  │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ Vector                       │
                    │ Collection / routing         │
                    │ Normalisation                │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
              ┌─────────────────────────────────────────┐
              │ OpenSearch                              │
              │ Search · correlation · investigation    │
              └──────────────────┬──────────────────────┘
                                 │
                     ┌───────────┴───────────┐
                     ▼                       ▼
              ElastAlert2               Analyst Search
              Detection                 & Investigation
                     │
                     ▼
        ┌───────────────────────────────────────────┐
        │ Enrichment / Investigation               │
        │ MISP · DFIR-IRIS · Velociraptor          │
        └────────────────────┬──────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ StackStorm SOAR │
                    │ Response logic  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Ollama + CrewAI │
                    │ Analyst assist  │
                    └─────────────────┘
```

The components are intentionally separated by responsibility so that a detection can be traced back to its telemetry source and forward into investigation and response.

---

## Engineering Objectives

### 1. Detection Engineering

Build detections that are:

- Mapped to MITRE ATT&CK techniques.
- Explicit about severity and detection logic.
- Testable with controlled telemetry.
- Reviewable as code/configuration.
- Able to document likely false positives.
- Suitable for iterative tuning rather than one-off demonstrations.

### 2. Threat Hunting

Start from a hypothesis and work backwards through available telemetry:

```text
Threat hypothesis
      ↓
ATT&CK technique / behaviour
      ↓
Required telemetry
      ↓
Search / query
      ↓
Pivot on user / host / IP / domain / process
      ↓
Determine malicious vs benign activity
      ↓
Create or tune detection
```

### 3. Incident Response

Turn an alert into an investigation rather than stopping at the alert itself:

```text
Alert
 ↓
Validate
 ↓
Scope
 ↓
Enrich
 ↓
Investigate
 ↓
Contain / respond
 ↓
Document
 ↓
Lessons learned
```

### 4. Adversary Emulation

Use controlled adversary scenarios to determine whether the SOC can observe and detect behaviours associated with common ATT&CK techniques.

### 5. Automation

Automate repeatable analyst actions while retaining clear boundaries around destructive or high-impact response actions.

### 6. AI-Assisted Analysis

Use local LLM capabilities to assist with triage, explanation, TTP mapping, hunting hypotheses and rule generation. AI output is treated as **analyst assistance**, not as authoritative evidence.

---

## End-to-End SOC Workflow

### Phase 1 — Generate activity

Controlled activity can be produced through the included simulation utility or through MITRE Caldera in the isolated lab.

### Phase 2 — Collect telemetry

Network and host-oriented telemetry is collected through the configured sensors and log sources.

### Phase 3 — Route and normalise

Vector provides the log-routing layer between sources and the SIEM.

### Phase 4 — Detect

ElastAlert2 rules evaluate OpenSearch data and generate detection events according to the configured rules.

### Phase 5 — Enrich

MISP can provide IOC/threat-intelligence context while analysts correlate activity across hosts, users, network indicators and ATT&CK techniques.

### Phase 6 — Investigate

DFIR-IRIS provides case tracking and investigation context; Velociraptor provides endpoint-oriented DFIR and VQL hunting capabilities.

### Phase 7 — Respond

StackStorm provides the automation layer for repeatable response workflows.

### Phase 8 — Validate

The same scenario is replayed or tested again to determine whether the detection is reliable and whether telemetry is sufficient.

### Phase 9 — Improve

Tune logic, reduce false positives, improve telemetry requirements and document the resulting detection change.

---

## Architecture

```text
                         LAB / TEST NETWORK
                                │
               ┌────────────────┴────────────────┐
               │                                 │
        MITRE Caldera                      Responder
        adversary emulation                red-team profile
               │                                 │
               └────────────────┬────────────────┘
                                ▼
                    ┌─────────────────────┐
                    │ Network / Host Data  │
                    │ Zeek · Suricata      │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Vector 0.38         │
                    │ Routing / transform │
                    └──────────┬──────────┘
                               ▼
              ┌─────────────────────────────────┐
              │ OpenSearch 2.13                │
              │ SIEM data store / investigation│
              └───────────────┬─────────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          ┌──────────────┐          ┌───────────────┐
          │ ElastAlert2  │          │ OpenSearch    │
          │ Detection    │          │ Dashboards    │
          └──────┬───────┘          └───────────────┘
                 │
                 ▼
       ┌─────────────────────────────┐
       │ Investigation & Enrichment  │
       │ MISP · DFIR-IRIS            │
       │ Velociraptor                │
       └──────────────┬──────────────┘
                      ▼
              ┌──────────────┐
              │ StackStorm   │
              │ SOAR         │
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │ Ollama       │
              │ + CrewAI     │
              │ AI assistance│
              └──────────────┘
```

Docker Compose provides the primary orchestration layer. Network-monitoring services that require raw packet access use host networking; the optional red-team profile is kept separate from the normal startup path.

---

## Tooling

| Capability | Component | Engineering role |
|---|---|---|
| SIEM | OpenSearch + Dashboards | Search, indexing, correlation and visual investigation |
| Log pipeline | Vector | Collection, routing and transformation |
| Detection engine | ElastAlert2 | Rule-based detection from OpenSearch |
| Network monitoring | Zeek | Protocol/network telemetry for hunting and detection |
| Network IDS | Suricata | Signature/IDS telemetry and EVE JSON |
| Threat intelligence | MISP | IOC and threat-intelligence enrichment |
| Case management | DFIR-IRIS | Incident/case tracking and investigation records |
| Endpoint DFIR | Velociraptor | VQL-based endpoint investigation |
| SOAR | StackStorm | Workflow and response automation |
| Adversary emulation | MITRE Caldera | Controlled ATT&CK-oriented activity |
| Red team testing | Responder | Isolated LLMNR/NBT-NS testing |
| Local AI | Ollama + CrewAI | Analyst-assisted analysis and workflow support |

---

## Detection Engineering

The repository contains 15 documented detection scenarios covering credential access, execution, persistence, lateral movement, discovery, command and control, collection, exfiltration and defense evasion.

| Detection scenario | ATT&CK | Severity |
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

### Detection-as-code workflow

```text
Detection idea
     ↓
ATT&CK mapping
     ↓
Sigma / ElastAlert2 rule
     ↓
Required telemetry defined
     ↓
Controlled event generation
     ↓
Rule validation
     ↓
Alert review
     ↓
False-positive analysis
     ↓
Rule tuning
     ↓
Regression test
```

The CI workflow validates YAML/configuration structure, Docker Compose syntax, Vector configuration and Python AI-agent code. This is intended to catch configuration errors before the complete lab is started.

---

## MITRE ATT&CK Coverage

The lab uses ATT&CK as the common language between attack simulation and defensive engineering.

| Tactic area | Example techniques represented |
|---|---|
| Initial Access | T1566.001 |
| Execution | T1059.001 |
| Persistence | T1053.005, T1547.001 |
| Credential Access | T1003.001, T1110.001, T1557.001 |
| Discovery | T1046 |
| Lateral Movement | T1021.002, T1550.002 |
| Command & Control | T1071.004 |
| Collection | T1039 |
| Exfiltration | T1041 |
| Defense Evasion | T1562.001 |

This mapping makes it possible to compare **what an emulation scenario attempted** with **what the detection layer actually observed**.

---

## Threat Hunting

The project supports a hypothesis-driven hunting model rather than simply searching for known alert names.

### Example hunting questions

- Are there unusual PowerShell execution patterns on a host?
- Is a workstation communicating with an unexpected external destination?
- Are multiple accounts receiving authentication failures from one source?
- Is SMB activity inconsistent with the normal role of a host?
- Are DNS requests showing characteristics associated with tunnelling?
- Has an endpoint generated activity associated with credential dumping?
- Are collection or archive behaviours occurring outside normal working patterns?

### Hunting pivots

```text
Source IP
  ↕
Destination IP / domain
  ↕
Host
  ↕
User
  ↕
Process / command
  ↕
ATT&CK technique
  ↕
IOC / MISP context
  ↕
Endpoint evidence / VQL
```

The objective is to teach analysts to pivot across multiple evidence types instead of relying on a single alert.

---

## Incident Response & DFIR

A useful investigation should establish **what happened, where it happened, how far it spread and what evidence supports the conclusion**.

### Investigation model

| Stage | Primary activity | Relevant component |
|---|---|---|
| Triage | Validate alert and severity | OpenSearch / ElastAlert2 |
| Scoping | Find related hosts/users/IPs | OpenSearch / Zeek / Suricata |
| Enrichment | Check IOCs and context | MISP |
| Case creation | Track incident state | DFIR-IRIS |
| Endpoint investigation | Collect/query endpoint evidence | Velociraptor |
| Response | Execute approved automation | StackStorm |
| Documentation | Record timeline and findings | DFIR-IRIS |
| Validation | Replay scenario / confirm coverage | Caldera / simulation |

### Analyst outcome

The desired result is not simply:

> `Alert = malicious`

It is a documented investigation containing:

- Detection that triggered.
- Initial evidence.
- Affected entities.
- ATT&CK techniques.
- Supporting IOCs.
- Investigation pivots.
- Scope determination.
- Response actions.
- Remaining uncertainty.
- Detection improvements identified during the investigation.

---

## Threat Intelligence

MISP is used as the threat-intelligence layer for the lab.

Typical workflow:

```text
IOC observed
   ↓
Normalise indicator
   ↓
Search / enrich in MISP
   ↓
Assess confidence and context
   ↓
Correlate with SIEM telemetry
   ↓
Associate with investigation
   ↓
Use result to improve detection/hunting
```

Threat intelligence is treated as **context**, not automatic proof of maliciousness. An IOC match should be evaluated alongside timing, host role, process activity, network behaviour and other evidence.

---

## Adversary Emulation

MITRE Caldera provides a controlled environment for exercising adversary behaviours and evaluating defensive visibility.

The project also includes a simulation utility for generating deterministic training telemetry:

```bash
./simulate-attack.sh apt29
./simulate-attack.sh bruteforce
./simulate-attack.sh insider
./simulate-attack.sh all
```

The built-in simulation utility **injects controlled events into OpenSearch for training and detection validation**. It is not a substitute for executing a real adversary technique on a test endpoint.

This distinction is important when interpreting evidence:

| Evidence type | What it demonstrates |
|---|---|
| Simulation event | Detection logic and analyst workflow against known test telemetry |
| Caldera operation | Controlled adversary-emulation activity |
| Native network sensor data | Actual observed network telemetry in the lab |
| Endpoint DFIR data | Actual evidence collected from a configured endpoint |

---

## SOAR & Automation

StackStorm is the response orchestration layer.

The engineering objective is to move repeatable work from manual analyst actions into controlled workflows:

```text
Detection
   ↓
Enrichment
   ↓
Decision / approval point
   ↓
Playbook
   ├── gather context
   ├── enrich indicators
   ├── create/update case
   ├── notify analyst
   └── perform approved response action
```

High-impact response actions should remain explicitly controlled in a lab environment. Automation should reduce repetitive work without hiding the decision path from the analyst.

---

## AI-Assisted SOC

The AI layer combines Ollama with CrewAI-based agents.

### Agent responsibilities

| Agent | Intended responsibility |
|---|---|
| Threat Analyst | Threat context, attribution hypotheses and TTP mapping |
| Incident Responder | Triage support and response-playbook suggestions |
| Threat Hunter | Hunting hypotheses and VQL query assistance |
| Detection Engineer | Detection/rule drafting and tuning assistance |

### AI operating model

```text
Security event
      ↓
Structured context
      ↓
AI-assisted analysis
      ↓
Hypotheses / suggestions
      ↓
Analyst verification
      ↓
Approved action / documented finding
```

The AI system should not be treated as an independent source of truth. Analysts should verify conclusions against SIEM, network, endpoint, case and intelligence evidence.

---

## Detection Validation

A detection is not considered useful simply because the rule parses successfully.

Validation should answer five questions:

1. **Telemetry:** Does the required event exist?
2. **Logic:** Does the rule identify the intended behaviour?
3. **Alerting:** Does the detection generate an actionable result?
4. **Quality:** Are false positives understood and manageable?
5. **Regression:** Does the detection continue to work after changes?

### Recommended validation loop

```bash
./health-check.sh
./simulate-attack.sh apt29
```

Then inspect OpenSearch, detection output and relevant investigation tooling before capturing evidence.

---

## Evidence & Screenshots

The repository contains 11 screenshot assets corresponding to the operational views below.

> **Evidence policy:** screenshots used as operational evidence should be captured from the running lab or from the repository's actual dashboard pages. AI-generated screenshots are not used as evidence.

### 01 — Command Center Portal

![SOC Lab Portal](dashboards/screenshots/00_portal.png)

### 02 — SOC Overview

![SOC Overview](dashboards/screenshots/01_soc_overview.png)

### 03 — OpenSearch SIEM

![OpenSearch SIEM](dashboards/screenshots/02_opensearch_siem.png)

### 04 — Zeek Network Monitoring

![Zeek Network](dashboards/screenshots/03_zeek_network.png)

### 05 — Suricata IDS

![Suricata IDS](dashboards/screenshots/04_suricata_ids.png)

### 06 — AI-Assisted SOC Analysis

![AI Agents](dashboards/screenshots/05_ai_agents.png)

### 07 — DFIR-IRIS Case Management

![DFIR-IRIS](dashboards/screenshots/06_iris_cases.png)

### 08 — MITRE Caldera

![Caldera](dashboards/screenshots/07_caldera_attack.png)

### 09 — MISP Threat Intelligence

![MISP](dashboards/screenshots/08_misp_ti.png)

### 10 — Velociraptor DFIR

![Velociraptor](dashboards/screenshots/09_velociraptor.png)

### 11 — Responder / Red Team

![Responder](dashboards/screenshots/10_responder_redteam.png)

### Screenshot provenance

The repository includes a Playwright-based capture workflow:

```bash
sudo ./setup.sh
./health-check.sh
./simulate-attack.sh apt29
./tools/capture-live-screenshots.sh
```

Selected native services:

```bash
./tools/capture-live-screenshots.sh --only 02_opensearch_siem,06_iris_cases,07_caldera_attack,08_misp_ti,09_velociraptor
```

Visible browser capture:

```bash
./tools/capture-live-screenshots.sh --headed
```

Strict reachability validation:

```bash
./tools/capture-live-screenshots.sh --strict
```

Each capture run writes `dashboards/screenshots/capture-manifest.json` with timestamp, source, reachability and result metadata. Full details are in [`docs/LIVE_SCREENSHOT_CAPTURE.md`](docs/LIVE_SCREENSHOT_CAPTURE.md).

---

## Requirements

| Requirement | Minimum | Recommended |
|---|---:|---:|
| RAM | 16 GB | 16–32 GB |
| Disk | 50 GB | 50+ GB |
| CPU | 4 cores | 8 cores |
| OS | Ubuntu 22.04 / Debian 12 / WSL2 / macOS | Ubuntu 22.04 LTS |
| Docker | 24.x | Current supported release |
| Docker Compose | v2.x | Current supported release |

Because OpenSearch, databases, telemetry processing and AI services can run simultaneously, resource usage depends heavily on the enabled services and local workload.

---

## Installation

### 1. Clone

```bash
git clone https://github.com/sandeepmothukuri/Enterprise-Detection-Engineering-SOC-Lab.git
cd Enterprise-Detection-Engineering-SOC-Lab
```

### 2. Make scripts executable

```bash
chmod +x setup.sh health-check.sh simulate-attack.sh tools/capture-live-screenshots.sh
```

### 3. Deploy

```bash
sudo ./setup.sh
```

The setup process performs preflight checks, generates local environment values where required, applies OpenSearch host tuning, pulls images and starts the stack in stages.

### 4. Verify

```bash
./health-check.sh
```

### 5. Generate training telemetry

```bash
./simulate-attack.sh apt29
```

### 6. Capture evidence

```bash
./tools/capture-live-screenshots.sh
```

---

## Configuration

Runtime secrets belong in `.env`, which is intentionally excluded from version control. The repository provides `.env.example` as the configuration template.

```bash
cp .env.example .env
```

Normally `setup.sh` performs the initial local environment generation and creates random values for several secrets. Required administrator credentials still need to be reviewed and set before deployment.

### Security requirements

- Never commit `.env`.
- Do not reuse production credentials.
- Change any default/service credentials before use.
- Keep the lab on a trusted or isolated network.
- Do not expose OpenSearch, MISP, IRIS, Caldera, Velociraptor, StackStorm or AI endpoints directly to the public internet.
- Keep Responder disabled unless you deliberately intend to run the isolated red-team profile.

---

## Attack Simulation

### APT-style training scenario

```bash
./simulate-attack.sh apt29
```

The scenario creates controlled ATT&CK-oriented events representing behaviours such as spearphishing, PowerShell execution, persistence, credential access, lateral movement, discovery, C2 and exfiltration.

### Brute-force / password-spray scenario

```bash
./simulate-attack.sh bruteforce
```

### Insider-threat training scenario

```bash
./simulate-attack.sh insider
```

### Run all supported scenarios

```bash
./simulate-attack.sh all
```

### Verify generated events

```bash
./simulate-attack.sh verify
```

These scenarios are for authorised lab testing and detection validation only.

---

## Service Endpoints

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

These endpoints are for local lab use. TLS certificate warnings may occur on locally generated HTTPS services.

---

## Optional Red-Team Profile

Responder is disabled by default because it requires raw network access and can interfere with networks outside the intended lab.

Start it only on an isolated test network:

```bash
docker compose --profile redteam up -d
```

Stop it when finished:

```bash
docker compose --profile redteam down
```

See [`docs/RESPONDER_KALI_GUIDE.md`](docs/RESPONDER_KALI_GUIDE.md) for the lab procedure.

---

## Live Screenshot Capture

The capture utility is deliberately local-first. It captures the actual browser-accessible interfaces rather than generating replacement images.

```bash
./tools/capture-live-screenshots.sh
```

### Capture selected services

```bash
./tools/capture-live-screenshots.sh --only 02_opensearch_siem,06_iris_cases,07_caldera_attack,08_misp_ti,09_velociraptor
```

### Headed capture

```bash
./tools/capture-live-screenshots.sh --headed
```

### Strict mode

```bash
./tools/capture-live-screenshots.sh --strict
```

Strict mode is useful before committing portfolio evidence because native-service reachability failures are treated as capture failures.

---

## Project Structure

```text
.
├── .github/
│   └── workflows/                  # CI validation
├── ai-agents/                      # CrewAI agents, API and supporting tools
│   ├── agents/
│   ├── crews/
│   └── tools/
├── config/                         # Service configuration
│   ├── caldera/
│   ├── elastalert2/
│   ├── nginx/
│   ├── opensearch/
│   ├── responder/
│   ├── stackstorm/
│   ├── suricata/
│   ├── vector/
│   └── zeek/
├── dashboards/                     # Analyst-facing dashboards
│   ├── screenshots/                # Evidence PNGs + capture manifest
│   └── *.html                      # Local evidence/dashboard pages
├── detection-rules/                # Detection-as-code
│   ├── sigma/
│   └── suricata/
├── docs/                           # Operational guides and evidence documentation
├── tools/                          # Health checks and screenshot automation
├── docker-compose.yml              # Multi-service lab orchestration
├── setup.sh                        # Environment/bootstrap automation
├── health-check.sh                 # Service health validation
├── simulate-attack.sh              # Controlled telemetry generation
├── SECURITY.md                     # Security policy
├── CONTRIBUTING.md                 # Contribution workflow
└── SPEC.md                         # Hardening/validation specification
```

---

## Security & Lab Safety

This repository is a **lab environment for learning and authorised testing**.

### Network isolation

Raw-packet services and red-team tooling should only be connected to a network you control. Responder is intentionally disabled by default.

### Credentials

Secrets and generated credentials should remain local. `.env` and sensitive keys are excluded through `.gitignore`.

### Data handling

Do not place real customer data, production credentials, private incident data or sensitive corporate telemetry into this public repository.

### Attack tooling

Caldera and Responder should only be used against systems where you have explicit authorisation to test. The included simulation utility is safer for repeatable detection demonstrations because it generates controlled telemetry rather than requiring a real compromise.

---

## Known Limitations

This project intentionally runs as a **single-machine security lab**, not as a production SOC deployment.

Important limitations include:

- Docker Compose is used for lab orchestration rather than production-scale container orchestration.
- Network-monitoring services require appropriate host-interface access and permissions.
- Endpoint telemetry quality depends on the endpoints actually connected to the lab.
- The built-in attack simulator creates controlled OpenSearch events; it does not reproduce every artefact of a real compromise.
- Local dashboard pages and native product UIs are different evidence sources and should not be treated as interchangeable.
- AI-generated analysis requires analyst verification.
- Resource consumption can become significant when the full stack is running simultaneously.
- Default configuration is intended for controlled local testing and requires security hardening before any broader deployment.

These limitations are documented deliberately so that the repository does not imply production certification or enterprise-scale performance from a workstation lab.

---

## Roadmap

### Detection Engineering

- [ ] Expand Sigma coverage across additional Windows and Linux behaviours.
- [ ] Add stronger regression testing for detection rules.
- [ ] Add detection-quality metrics such as precision, false-positive rate and coverage tracking.
- [ ] Add more explicit telemetry prerequisites to each detection.

### Telemetry & SIEM

- [ ] Improve field normalisation across Zeek, Suricata and host telemetry.
- [ ] Add richer OpenSearch dashboards backed by live indices.
- [ ] Add retention and index-lifecycle examples for larger datasets.

### Threat Hunting & DFIR

- [ ] Expand reusable VQL hunting packs.
- [ ] Add documented investigation playbooks for each major scenario.
- [ ] Add more endpoint/network pivot examples.

### SOAR

- [ ] Expand StackStorm playbooks for enrichment and case-management workflows.
- [ ] Add analyst approval gates for higher-impact actions.
- [ ] Add response audit logging examples.

### AI

- [ ] Improve structured input/output contracts for SOC agents.
- [ ] Add confidence and provenance fields to AI responses.
- [ ] Add evaluation datasets for triage and detection-rule generation.
- [ ] Add stronger guardrails around automated actions.

### Evidence

- [ ] Replace stale portfolio screenshots with freshly captured native-tool evidence after each major lab change.
- [ ] Keep screenshot manifests alongside committed evidence.
- [ ] Add repeatable evidence capture to a self-hosted CI runner when a suitable lab runner is available.

---

## Documentation

| Document | Purpose |
|---|---|
| [`docs/LIVE_SCREENSHOT_CAPTURE.md`](docs/LIVE_SCREENSHOT_CAPTURE.md) | Screenshot capture, provenance and evidence workflow |
| [`docs/RESPONDER_KALI_GUIDE.md`](docs/RESPONDER_KALI_GUIDE.md) | Isolated Responder lab procedure |
| [`docs/SECURITY_ONION_VM_GUIDE.md`](docs/SECURITY_ONION_VM_GUIDE.md) | Security Onion VM guidance |
| [`SECURITY.md`](SECURITY.md) | Vulnerability reporting and lab security policy |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Contribution and change workflow |
| [`SPEC.md`](SPEC.md) | Repository hardening and validation specification |

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
- Email: sandeep.mothukuris@gmail.com

---

## License

MIT License. See [`LICENSE`](LICENSE).

Copyright (c) 2026 Sandeep Mothukuri
