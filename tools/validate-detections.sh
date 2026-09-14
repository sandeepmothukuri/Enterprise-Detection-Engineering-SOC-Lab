#!/usr/bin/env bash
# Static validation for the detection and deployment layer.
set -euo pipefail

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE=".env.example"

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

printf '[1/8] Compose syntax and service references\n'
docker compose --env-file "$ENV_FILE" config --quiet
pass 'docker-compose.yml'

printf '[2/8] Shell syntax\n'
while IFS= read -r -d '' file; do
  bash -n "$file"
done < <(find . -type f -name '*.sh' -not -path './.git/*' -print0)
pass 'all shell scripts parse'

printf '[3/8] Sigma rules\n'
python3 - <<'PY'
from pathlib import Path
import re
import yaml

root = Path('detection-rules/sigma')
files = sorted(root.rglob('*.yml'))
if not files:
    raise SystemExit('no Sigma rules found')

uuid_re = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$')
ids = set()
count = 0
for path in files:
    docs = list(yaml.safe_load_all(path.read_text()))
    for doc in docs:
        if not isinstance(doc, dict):
            raise SystemExit(f'{path}: document is not a mapping')
        for key in ('title', 'id', 'status', 'description', 'author', 'date', 'tags', 'falsepositives', 'level'):
            if key not in doc:
                raise SystemExit(f'{path}: missing {key}')
        if not uuid_re.match(str(doc['id'])):
            raise SystemExit(f'{path}: invalid UUID: {doc["id"]}')
        if doc['id'] in ids:
            raise SystemExit(f'duplicate Sigma id: {doc["id"]}')
        ids.add(doc['id'])
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(doc['date'])):
            raise SystemExit(f'{path}: date must be YYYY-MM-DD')
        tags = doc.get('tags') or []
        if not any(str(tag).startswith('attack.') for tag in tags):
            raise SystemExit(f'{path}: missing ATT&CK tag')
        if 'correlation' in doc:
            corr = doc['correlation']
            for key in ('type', 'rules', 'timespan', 'condition'):
                if key not in corr:
                    raise SystemExit(f'{path}: correlation missing {key}')
        else:
            for key in ('logsource', 'detection'):
                if key not in doc:
                    raise SystemExit(f'{path}: missing {key}')
        count += 1
print(f'PASS: {count} Sigma documents parsed and metadata-validated')
PY

printf '[4/8] ElastAlert2 rules\n'
python3 - <<'PY'
from pathlib import Path
import yaml

required = {'name', 'type', 'index', 'filter', 'alert'}
valid_types = {'any', 'blacklist', 'whitelist', 'change', 'frequency', 'flatline', 'spike', 'metric_aggregation', 'cardinality', 'percentage_match', 'new_term'}
files = sorted(Path('config/elastalert2/rules').rglob('*.yml'))
if not files:
    raise SystemExit('no ElastAlert2 rules found')
for path in files:
    data = yaml.safe_load(path.read_text())
    missing = required - set(data)
    if missing:
        raise SystemExit(f'{path}: missing {sorted(missing)}')
    if data['type'] not in valid_types:
        raise SystemExit(f'{path}: unsupported rule type {data["type"]}')
    if not str(data['index']).startswith('soc-logs-'):
        raise SystemExit(f'{path}: unexpected index {data["index"]}')
    alerts = data['alert'] if isinstance(data['alert'], list) else [data['alert']]
    if 'post' in alerts and not data.get('http_post_url'):
        raise SystemExit(f'{path}: post alert missing http_post_url')
print(f'PASS: {len(files)} ElastAlert2 rules parsed and structurally validated')
PY

printf '[5/8] Python syntax\n'
python3 - <<'PY'
from pathlib import Path
import py_compile
files = sorted(Path('.').rglob('*.py'))
for path in files:
    if '.git' in path.parts:
        continue
    py_compile.compile(str(path), doraise=True)
print(f'PASS: {len(files)} Python files compile')
PY

printf '[6/8] Environment template and secret hygiene\n'
python3 - <<'PY'
from pathlib import Path
import re
text = Path('.env.example').read_text()
keys = [line.split('=', 1)[0] for line in text.splitlines() if line and not line.startswith('#') and '=' in line]
required = {
    'OPENSEARCH_INITIAL_ADMIN_PASSWORD', 'IRIS_SECRET_KEY', 'IRIS_ADMIN_PASSWORD',
    'IRIS_ADM_API_KEY', 'IRIS_DB_PASSWORD', 'MISP_ADMIN_PASSWORD', 'MISP_DB_PASSWORD',
    'MISP_MYSQL_ROOT_PASSWORD', 'VELOX_PASSWORD', 'CALDERA_RED_PASS', 'CALDERA_BLUE_PASS',
    'ST2_AUTH_TOKEN', 'CREWAI_API_PORT', 'OLLAMA_MODEL'
}
missing = required - set(keys)
if missing:
    raise SystemExit(f'.env.example missing {sorted(missing)}')
for forbidden in ('OPENSEARCH_PASSWORD=', 'IRIS_API_KEY='):
    if forbidden in text:
        raise SystemExit(f'obsolete environment variable present: {forbidden}')
print(f'PASS: .env.example contains {len(keys)} variables and canonical names')
PY
if git grep -nE '-----BEGIN (RSA |EC |)PRIVATE KEY-----|password[[:space:]]*[:=][[:space:]]*[A-Za-z0-9!@#$%^&*]{8,}' -- ':!*.md' ':!.env.example' >/tmp/soc-secret-scan.txt 2>/dev/null; then
  cat /tmp/soc-secret-scan.txt
  fail 'possible committed secret material found'
fi
pass 'no obvious private-key or hard-coded credential material'

printf '[7/8] Vector configuration\n'
python3 - <<'PY'
from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:
    raise SystemExit('Python 3.11+ is required for TOML validation')
data = tomllib.loads(Path('config/vector/vector.toml').read_text())
assert 'sources' in data and 'sinks' in data
print(f'PASS: Vector TOML parsed ({len(data["sources"])} sources, {len(data["sinks"])} sinks)')
PY

printf '[8/8] OpenSearch certificate references\n'
for file in config/opensearch/opensearch-node1.yml config/opensearch/opensearch-node2.yml; do
  grep -q 'pemcert_filepath' "$file" || fail "$file missing node certificate reference"
  grep -q 'pemtrustedcas_filepath' "$file" || fail "$file missing CA reference"
  grep -q 'authcz.admin_dn' "$file" || fail "$file missing admin DN"
  ! grep -q 'allow_unsafe_democertificates' "$file" || fail "$file still enables demo certificates"
done
pass 'OpenSearch node TLS configuration is security-hardened'

echo 'All static detection/deployment validations passed.'
