# SOC Lab audit

Audit date: 2026-09-14

## Findings

| Severity | Finding | Status |
| --- | --- | --- |
| HIGH | Setup used non-existent Compose services (`iris`, `ai-agents`) and container `ollama`; OpenSearch checks used the wrong variable and HTTP instead of HTTPS. | Fixed in `setup.sh`. |
| HIGH | CrewAI listened on container port 8000 while Compose published container port 8500, making the host API unreachable. | Fixed by publishing `${CREWAI_API_PORT}:8000`. |
| MEDIUM | Health checks used a raw `responder` container name instead of resolving the Compose service and setup output listed stale IRIS, MISP, and AI URLs. | Fixed in `health-check.sh`, `setup.sh`, and the AI dashboard link. |
| HIGH | Attack simulation used the wrong `.env` key and HTTP against the TLS-enabled OpenSearch endpoint. | Fixed in `simulate-attack.sh`. |
| HIGH | CloudTrail Vector example contained a usable default OpenSearch password. | Removed; `OPENSEARCH_PASSWORD` is now required. |
| HIGH | CI security scan only warned about a known default credential and did not fail. | CI now fails on sentinel/default credentials. |
| MEDIUM | Several Compose images use mutable `latest` tags, reducing reproducibility. | Remaining blocker; pin to verified release tags or digests before production use. |
| MEDIUM | Compose references optional `config/velociraptor`, `attack-simulation/caldera`, and `attack-simulation/responder` paths that are not present in this checkout. | Remaining blocker; enable those integrations only after supplying the upstream configs/content. |
| MEDIUM | Publicly published service ports and the AI API's wildcard CORS are appropriate for a local lab but unsafe on an untrusted network. | Remaining blocker; restrict host bindings and configure an allowlist before shared deployment. |
| HIGH | StackStorm `block_ip` interpolated the requested IP into `shell=True`, did not validate direction/duration, and scheduled only inbound cleanup. | Fixed with IP validation, argv-based commands, rollback, and complete cleanup scheduling; covered by `tools/test-block-ip-action.py`. |
| LOW | The repository has no full-service integration test because it requires Docker, generated certificates, and all external images. | Targeted static checks remain available in CI and `tools/validate-detections.sh`. |

## Scope and validation

README files and README-referenced screenshots were not modified. No services were started during this audit. Validation should run `docker compose --env-file .env.example config --quiet` where Docker is available, followed by the CI checks and the focused scripts in `tools/`.
