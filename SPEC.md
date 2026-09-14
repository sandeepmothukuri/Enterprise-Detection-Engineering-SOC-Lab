# Enterprise Detection SOC Lab hardening

§G
Fix verified credential, Compose, CI, detection-config gaps; leave local reviewable tree.

§C
⊥ commit/push/PR/remote change; preserve lab services; no real/default usable credentials; validate without full lab start.

§I
env: `.env.example` → required local config placeholders.
docker: `docker compose config` → valid service graph.
cmd: `./setup.sh` → local `.env` generation.
config: Sigma/ElastAlert/Vector → CI validation.
api: `GET /health` AI agents → health response.

§V
V1: committed config/code ⊥ usable default credential; secret env var required or startup fails clear.
V2: `.env.example` values → explicit placeholders; setup generates secrets locally.
V3: ∀ Compose build service → checked-in context & Dockerfile.
V4: CI validates YAML, Compose, Python syntax; no false-success lint pipeline.
V5: Sigma/ElastAlert rules retain title, detection/log source, severity, ATT&CK, false positives.
V6: README setup/ports/env paths → checked-in files & Compose.
V7: no full lab start required for config validation.
V8: setup generates all Compose-mounted OpenSearch certificates before any OpenSearch container starts.
V9: detection validation normalizes Docker bind-mount paths for Git Bash/Windows and keeps POSIX paths unchanged.
V10: SOAR blocking actions validate IP/direction input, never interpolate it into a shell, and schedule cleanup for every applied rule.
V11: repository validators test the actual mounted Vector configuration and live Zeek tests fail fast when the service is stopped.
V12: executable shell files mounted into Linux containers use LF line endings and a valid Linux shebang.
V13: live Zeek T1046 validation runs the pinned image with repository scripts mounted at the image's actual installation path and generates traffic in a capture-visible namespace.

§T
id|status|task|cites
T1|.|remove usable credential defaults; add focused config tests|V1,V2
T2|.|fix Compose build contexts/service wiring|V3,V7
T3|.|fix CI validation reliability; validate detection config|V4,V5,V7
T4|.|sync README security/setup claims|V2,V6
T5|.|run final local validation; leave diff uncommitted|V1,V2,V3,V4,V5,V6,V7
T6|.|generate OpenSearch TLS certificates before Compose startup|V8

§B
id|date|cause|fix
B1|2026-09-14|Compose mounted absent OpenSearch certificate paths, so WSL2 never generated pem files and the plugin failed at startup|Generate idempotent host certificates before Compose startup; add focused test
B2|2026-09-14|Git Bash rewrote validator bind mounts to the Git installation path, so Zeek could not load the mounted config|V9; normalize Windows Docker paths and add portability test
B3|2026-09-14|StackStorm block_ip interpolated unvalidated input into shell=True and cleaned up only inbound rules|V10; validate inputs, use argv execution, roll back partial blocks, and schedule all cleanup rules
B4|2026-09-14|Vector validation inspected no repository file and Zeek T1046 looped against a stopped container|V11; mount the actual Vector file and fail fast on Zeek service state
B5|2026-09-14|Windows CRLF in the mounted Zeek entrypoint made Linux Docker report no such file or directory|V12; normalize the entrypoint to LF and add a line-ending regression test
B6|2026-09-14|Zeek live test mounted repository scripts under a nonexistent image path and generated bridge traffic invisible to Docker Desktop packet capture|V13; use /usr/local/zeek and shared-loopback live traffic in a pinned temporary sensor
