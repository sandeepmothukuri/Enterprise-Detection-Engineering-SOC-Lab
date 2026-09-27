# Platform Health, Microservice Topology & Pipeline Telemetry

Author: Sandeep Mothukuri ([@sandeepmothukuri](https://github.com/sandeepmothukuri))  
Platform: Enterprise Detection Engineering & SOC Operations Lab v2

---

## 1. Stack Service Topology & Port Allocation

The platform orchestrates 12 dedicated microservices deployed across Docker networks `soc-net` (`172.20.0.0/16`) and `red-team`:

| Service / Container Name | Role | Primary Port(s) | Healthcheck Method |
| :--- | :--- | :--- | :--- |
| `soc-opensearch-1` | Primary SIEM Cluster Node | `9200` (HTTPS) | OpenSearch Cluster Health API (`_cluster/health`) |
| `soc-opensearch-2` | Secondary SIEM Cluster Node | `9200` (Internal) | Node Join & Cluster State Validation |
| `soc-dashboards` | OpenSearch Visual UI | `5601` (HTTP) | OpenSearch Dashboards `/api/status` |
| `soc-vector` | High-Throughput Log Aggregator| `9000` (TCP), `514` (UDP) | Vector Internal API (`/health`) |
| `soc-zeek` | Network Security Monitor | `Internal Tap` | Packet capture socket & log rotation |
| `soc-suricata` | IDS / IPS Threat Engine | `Internal Tap` | Suricata stats.log validation |
| `soc-elastalert` | Detection & Alerting Engine | Internal Daemon | Rule test execution & OpenSearch connectivity |
| `soc-dfir-iris` | Incident Response Platform | `8000` (HTTP) | Web API ping (`/api/v1/ping`) |
| `soc-misp` | Threat Intel Sharing Platform | `8443` (HTTPS) | Web UI / PyMISP authentication test |
| `soc-velociraptor`| Live Forensic & VQL Server | `8889` (HTTPS GUI) | Velociraptor TLS listener check |
| `soc-caldera` | Adversary Emulation Engine | `8888` (HTTP) | Caldera Core REST API |
| `soc-ollama` | Local AI LLM Engine | `11434` (HTTP) | Ollama API model list (`/api/tags`) |

---

## 2. Ingestion Throughput & Reliability KPIs

- **Baseline Ingestion Rate**: ~450–1,200 Events Per Second (EPS)
- **Peak Attack Simulation Burst**: ~3,500 EPS
- **Vector Ingestion Buffer**: Disk-backed memory FIFO buffer with zero drop guarantee
- **OpenSearch Sharding**: 2 Primary Shards + 1 Replica per daily index
