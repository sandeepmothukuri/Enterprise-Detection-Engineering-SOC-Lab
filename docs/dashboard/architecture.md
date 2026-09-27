# SOC Platform Dashboard Architecture

Author: Sandeep Mothukuri ([@sandeepmothukuri](https://github.com/sandeepmothukuri))  
Platform: Enterprise Detection Engineering & SOC Operations Lab v2

---

## 1. Architectural Overview

The **Enterprise SOC Operations Platform** implements a high-throughput, low-latency telemetry ingestion and detection engineering pipeline. The visualization tier provides a single pane of glass spanning executive visibility, deep analyst investigation, purple team validation, and autonomous AI triage.

```mermaid
flowchart TD
    subgraph DataSources["Telemetry Sources"]
        Sysmon["Windows Sysmon & Event Logs"]
        Zeek["Zeek NSM (Conn, DNS, TLS, HTTP)"]
        Suricata["Suricata 7.0 IDS (EVE JSON)"]
        Auditd["Linux Auditd & Auth Logs"]
        Caldera["Caldera Adversary Emulation"]
    end

    subgraph Ingestion["Pipeline & Ingestion Tier"]
        Vector["Vector Aggregator (Port 9000/9001/514)"]
        Transforms["VRL Remap, Field Normalization & MITRE Enrichment"]
    end

    subgraph StorageEngine["Storage & Detection Tier"]
        OpenSearch["OpenSearch Cluster (Nodes 1 & 2)"]
        ElastAlert["ElastAlert2 Real-Time Detection Engine"]
        Sigma["13 Compiled Sigma Rules (2026 Edition)"]
    end

    subgraph AutonomousAI["Autonomous AI SOC Tier"]
        CrewAI["CrewAI Multi-Agent Engine"]
        Ollama["Local LLM (Llama 3 / Mistral)"]
        IRIS["DFIR-IRIS Case Management API"]
    end

    subgraph PresentationTier["9-Tier Operations Interface"]
        D1["Tier 1: SOC Command Center"]
        D2["Tier 2: Incident Operations"]
        D3["Tier 3: Detection Engineering"]
        D4["Tier 4: MITRE ATT&CK Matrix"]
        D5["Tier 5: Threat Hunting Sandbox"]
        D6["Tier 6: Network Security & NSM"]
        D7["Tier 7: Endpoint Security & Forensics"]
        D8["Tier 8: Autonomous AI SOC Triage"]
        D9["Tier 9: Platform Health & Reliability"]
    end

    DataSources --> Vector
    Vector --> Transforms
    Transforms --> OpenSearch
    OpenSearch --> ElastAlert
    Sigma --> ElastAlert
    ElastAlert --> IRIS
    ElastAlert --> CrewAI
    CrewAI <--> Ollama
    CrewAI --> IRIS
    OpenSearch --> PresentationTier
```

---

## 2. 9-Tier Operational Hierarchy

1. **SOC Command Center (`01_soc_command_center.html`)**:
   - Executive telemetry metrics: Total Ingested Events (EPS), Active Incidents Queue, Severity Distribution, Top Target Assets.
2. **Incident Operations (`02_incident_operations.html`)**:
   - Live alert triage stream, DFIR-IRIS case status tracking, chronological kill chain reconstruction.
3. **Detection Engineering (`03_detection_engineering.html`)**:
   - Sigma rule catalog (13 rules), test harness CI/CD validation results, detection coverage across MITRE tactics.
4. **MITRE ATT&CK Matrix (`04_mitre_attack.html`)**:
   - Enterprise ATT&CK matrix heatmap, technique frequency breakdown, adversary emulation test mappings.
5. **Threat Hunting (`05_threat_hunting.html`)**:
   - Advanced outlier analysis, Velociraptor VQL artifact inspection, rare process execution anomalies, MISP IOC pivoting.
6. **Network Security (`06_network_security.html`)**:
   - Zeek connection logs, Suricata IDS alert signatures, DNS tunneling detection, TLS certificate analysis.
7. **Endpoint Security (`07_endpoint_security.html`)**:
   - Windows Sysmon process trees (Event 1), LSASS memory access (Event 10), Remote Thread injection (Event 8), Linux Auditd privilege escalations.
8. **AI SOC (`08_ai_soc.html`)**:
   - CrewAI autonomous multi-agent triage logs, verdict confidence scores, false positive suppression, analyst escalation queue.
9. **Platform Health (`09_platform_health.html`)**:
   - Microservice health for all 12 Docker containers, Vector ingestion EPS, OpenSearch index sizing, queue latency.
