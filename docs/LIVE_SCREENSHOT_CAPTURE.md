# Live SOC Screenshot Capture

This repository now includes a Playwright-based evidence capture utility. It is designed to capture screenshots from the **running SOC lab**, not to manufacture dashboard evidence.

## What is captured

| File | Source |
|---|---|
| `00_portal.png` | Local command-center portal |
| `01_soc_overview.png` | Local SOC overview page |
| `02_opensearch_siem.png` | **Native OpenSearch Dashboards UI** |
| `03_zeek_network.png` | Local Zeek evidence view |
| `04_suricata_ids.png` | Local Suricata evidence view |
| `05_ai_agents.png` | Local AI-agent view |
| `06_iris_cases.png` | **Native DFIR-IRIS UI** |
| `07_caldera_attack.png` | **Native MITRE Caldera UI** |
| `08_misp_ti.png` | **Native MISP UI** |
| `09_velociraptor.png` | **Native Velociraptor UI** |
| `10_responder_redteam.png` | Local Responder evidence view |

Zeek, Suricata and Responder do not provide a comparable browser dashboard in this lab configuration, so their screenshots remain project evidence views. They must only be described as live evidence when their underlying telemetry/logs are populated by the running lab.

## Capture

Start the lab and generate controlled telemetry first:

```bash
sudo ./setup.sh
./health-check.sh
./simulate-attack.sh apt29
```

Then install the screenshot dependencies and capture:

```bash
./tools/capture-live-screenshots.sh
```

The script uses a fixed 1600×1000 Chromium viewport and saves PNG evidence under `dashboards/screenshots/`. Playwright supports full-page screenshots and repeatable captures with animations disabled.

### Capture only selected tools

```bash
./tools/capture-live-screenshots.sh --only 02_opensearch_siem,07_caldera_attack,08_misp_ti
```

### See the browser while capturing

```bash
./tools/capture-live-screenshots.sh --headed
```

### Require all native services to be reachable

```bash
./tools/capture-live-screenshots.sh --strict
```

## Evidence manifest

Every run creates:

```text
dashboards/screenshots/capture-manifest.json
```

The manifest records:

- UTC capture timestamp
- screenshot path
- source URL
- native-tool vs repository-dashboard source type
- HTTP reachability/status where applicable
- capture success/failure

This makes the screenshot provenance auditable instead of relying on README claims.

## Important distinction

A screenshot being successfully captured proves that a page was reachable. It does **not** by itself prove that the underlying data is genuine. Before taking portfolio screenshots, run the lab, execute the controlled attack simulation, verify OpenSearch/Zeek/Suricata/IRIS/MISP/Caldera/Velociraptor telemetry, and then capture the evidence.

Do not replace a native-tool screenshot with an AI-generated image or a fabricated alert feed.

## CI / artifact option

The capture utility is intentionally local-first because the Docker SOC lab and its telemetry are normally running on the analyst's machine. If a self-hosted runner is later used, the generated PNGs and manifest can also be uploaded as GitHub Actions artifacts.
