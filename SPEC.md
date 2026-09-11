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

§T
id|status|task|cites
T1|.|remove usable credential defaults; add focused config tests|V1,V2
T2|.|fix Compose build contexts/service wiring|V3,V7
T3|.|fix CI validation reliability; validate detection config|V4,V5,V7
T4|.|sync README security/setup claims|V2,V6
T5|.|run final local validation; leave diff uncommitted|V1,V2,V3,V4,V5,V6,V7

§B
id|date|cause|fix
