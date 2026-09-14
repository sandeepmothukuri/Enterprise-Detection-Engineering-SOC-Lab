#!/usr/bin/env bash
set -euo pipefail

entrypoint="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/zeek-entrypoint.sh"
first_line="$(head -n 1 "$entrypoint")"

[[ "$first_line" == "#!/bin/sh" ]] || {
  echo "FAIL: Zeek entrypoint must use a POSIX shell shebang" >&2
  exit 1
}

if LC_ALL=C grep -q $'\r' "$entrypoint"; then
  echo "FAIL: Zeek entrypoint contains CRLF line endings" >&2
  exit 1
fi

echo "Zeek entrypoint portability test passed"
