#!/usr/bin/env python3
"""Capture evidence screenshots from the running SOC lab.

This script intentionally does NOT fabricate dashboard data. Native tool UIs are
captured when the corresponding service is reachable; the remaining project
views are captured from the repository's local dashboard pages.

Usage:
  python3 tools/capture-live-screenshots.py
  python3 tools/capture-live-screenshots.py --headed
  python3 tools/capture-live-screenshots.py --only 02_opensearch_siem,07_caldera_attack
  python3 tools/capture-live-screenshots.py --strict

Requirements:
  pip install -r tools/requirements-screenshots.txt
  python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import URLError
from urllib.request import Request, urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "dashboards"
OUT = DASHBOARDS / "screenshots"

# Native screenshots use the real tool UI. Local views are retained for sensors
# without a web UI (Zeek, Suricata, Responder) and for the project command center.
TARGETS = [
    {"id": "00_portal", "label": "Command Center Portal", "kind": "local", "path": "index.html"},
    {"id": "01_soc_overview", "label": "SOC Overview", "kind": "local", "path": "01_soc_overview.html"},
    {"id": "02_opensearch_siem", "label": "OpenSearch Dashboards", "kind": "native", "url": "${OPENSEARCH_DASHBOARDS_URL:-http://127.0.0.1:5601}"},
    {"id": "03_zeek_network", "label": "Zeek Network Evidence View", "kind": "local", "path": "03_zeek_network.html"},
    {"id": "04_suricata_ids", "label": "Suricata IDS Evidence View", "kind": "local", "path": "04_suricata_ids.html"},
    {"id": "05_ai_agents", "label": "AI Agents", "kind": "local", "path": "05_ai_agents.html"},
    {"id": "06_iris_cases", "label": "DFIR-IRIS", "kind": "native", "url": "${IRIS_URL:-https://127.0.0.1:8443}"},
    {"id": "07_caldera_attack", "label": "MITRE Caldera", "kind": "native", "url": "${CALDERA_URL:-http://127.0.0.1:8888}"},
    {"id": "08_misp_ti", "label": "MISP", "kind": "native", "url": "${MISP_URL:-http://127.0.0.1:8080}"},
    {"id": "09_velociraptor", "label": "Velociraptor", "kind": "native", "url": "${VELOCIRAPTOR_URL:-https://127.0.0.1:8889}"},
    {"id": "10_responder_redteam", "label": "Responder Evidence View", "kind": "local", "path": "10_responder_redteam.html"},
]


def expand_env(value: str) -> str:
    import re

    def repl(match: re.Match[str]) -> str:
        name, default = match.group(1), match.group(2)
        return os.getenv(name, default or "")

    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}", repl, value)


def reachable(url: str, timeout: float = 4.0) -> tuple[bool, int | None, str | None]:
    try:
        req = Request(url, headers={"User-Agent": "SOC-Lab-Screenshot-Capture/1.0"})
        with urlopen(req, timeout=timeout, context=__import__("ssl")._create_unverified_context()) as r:
            return True, r.status, None
    except Exception as exc:  # service may return 401/302 and still be alive
        if isinstance(exc, URLError) and getattr(exc, "code", None):
            return True, exc.code, None
        return False, None, str(exc)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def start_local_server() -> tuple[ThreadingHTTPServer, Thread]:
    # Bind only to loopback; this is a local evidence utility.
    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    server.RequestHandlerClass.directory = str(DASHBOARDS)
    # SimpleHTTPRequestHandler reads cwd when directory isn't passed by class.
    os.chdir(DASHBOARDS)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headed", action="store_true", help="show Chromium while capturing")
    parser.add_argument("--strict", action="store_true", help="fail if any native service is unreachable")
    parser.add_argument("--only", help="comma-separated target IDs")
    parser.add_argument("--wait", type=float, default=2.5, help="seconds to wait after page load")
    args = parser.parse_args()

    selected = {x.strip() for x in args.only.split(",")} if args.only else None
    targets = [t for t in TARGETS if not selected or t["id"] in selected]
    OUT.mkdir(parents=True, exist_ok=True)

    local_server, _ = start_local_server()
    local_base = f"http://127.0.0.1:{local_server.server_port}"
    manifest = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "capture_mode": "real-service-or-local-project-view",
        "repository": "sandeepmothukuri/Enterprise-Detection-Engineering-SOC-Lab",
        "targets": [],
    }
    failures = 0

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=not args.headed)
            context = browser.new_context(
                viewport={"width": 1600, "height": 1000},
                device_scale_factor=1,
                ignore_https_errors=True,
            )
            context.set_default_timeout(15000)

            for target in targets:
                item = dict(target)
                item["captured_at_utc"] = datetime.now(timezone.utc).isoformat()
                item["screenshot"] = f"dashboards/screenshots/{target['id']}.png"

                if target["kind"] == "local":
                    url = f"{local_base}/{target['path']}"
                    item["source"] = url
                    item["source_type"] = "repository dashboard"
                else:
                    url = expand_env(target["url"])
                    item["source"] = url
                    item["source_type"] = "native tool UI"
                    ok, status, error = reachable(url)
                    item["reachable"] = ok
                    item["http_status"] = status
                    if not ok:
                        item["error"] = error
                        failures += 1
                        print(f"[SKIP] {target['id']}: {url} ({error})")
                        manifest["targets"].append(item)
                        continue

                page = context.new_page()
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(int(args.wait * 1000))
                    page.screenshot(
                        path=str(OUT / f"{target['id']}.png"),
                        full_page=True,
                        animations="disabled",
                    )
                    item["captured"] = True
                    print(f"[OK]   {target['id']} <- {url}")
                except Exception as exc:
                    item["captured"] = False
                    item["error"] = str(exc)
                    failures += 1
                    print(f"[FAIL] {target['id']}: {exc}")
                finally:
                    page.close()
                manifest["targets"].append(item)

            browser.close()
    finally:
        local_server.shutdown()
        local_server.server_close()

    manifest_path = OUT / "capture-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"\nManifest: {manifest_path}")
    print(f"Screenshots: {OUT}")

    if failures and args.strict:
        print(f"\n{failures} target(s) failed. Strict mode enabled.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
