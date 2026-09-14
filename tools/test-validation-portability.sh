#!/usr/bin/env bash
set -euo pipefail

script="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/validate-detections.sh"
grep -Fq 'cygpath -m "$ROOT_DIR"' "$script"
grep -Fq 'export MSYS_NO_PATHCONV=1' "$script"
grep -Fq '"$DOCKER_ROOT/config/zeek' "$script"
grep -Fq '"$DOCKER_ROOT/config/suricata' "$script"
grep -Fq '"$DOCKER_ROOT/detection-rules/suricata' "$script"
echo "Detection validator Docker path portability test passed"
