#!/usr/bin/env python3
"""
Shared utilities and resilient HTTP sessions for SOAR playbooks.
"""

import os
import json
import logging
from datetime import datetime, timezone
import urllib3
import requests

# Suppress self-signed certificate warnings for local lab environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("soar_workflows")

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://opensearch-node1:9200")
OPENSEARCH_PASS = os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD", os.getenv("OPENSEARCH_PASSWORD", ""))
MISP_URL = os.getenv("MISP_URL", "http://misp:80")
IRIS_URL = os.getenv("IRIS_URL", "https://dfir-iris:443")
ST2_URL = os.getenv("ST2_URL", "http://stackstorm:9101")
VELOCI_URL = os.getenv("VELOCI_URL", "https://velociraptor:8889")
CALDERA_URL = os.getenv("CALDERA_URL", "http://caldera:8888")

DEFAULT_HEADERS = {"Content-Type": "application/json"}


def get_authenticated_session() -> requests.Session:
    """Create a configured requests Session with SSL warning suppression and default timeouts."""
    session = requests.Session()
    session.verify = False
    if OPENSEARCH_PASS:
        session.auth = ("admin", OPENSEARCH_PASS)
    return session


def log_soc_action(action: str, details: dict, playbook_name: str, mitre_technique: str = "") -> bool:
    """Record an automated defensive response action into the soc-actions index in OpenSearch."""
    event = {
        "action": action,
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "playbook": playbook_name,
        "mitre_technique": mitre_technique,
        **details
    }
    session = get_authenticated_session()
    try:
        r = session.post(
            f"{OPENSEARCH_URL}/soc-actions/_doc",
            headers=DEFAULT_HEADERS,
            json=event,
            timeout=5
        )
        return r.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"Could not log action to OpenSearch: {e}")
        return False


def enrich_ip_misp(ip: str, misp_key: str = "") -> dict:
    """Query MISP attributes for known threat intelligence on a given IP."""
    key = misp_key or os.getenv("MISP_KEY", "")
    if not key:
        return {"hits": 0, "malicious": False, "tags": [], "note": "No MISP API key provided"}

    session = requests.Session()
    session.verify = False
    try:
        r = session.post(
            f"{MISP_URL}/attributes/restSearch",
            headers={**DEFAULT_HEADERS, "Authorization": key},
            json={"value": ip, "type": "ip-src"},
            timeout=10
        )
        attrs = r.json().get("response", {}).get("Attribute", [])
        return {
            "hits": len(attrs),
            "malicious": len(attrs) > 0,
            "tags": [a.get("value") for a in attrs[:5]]
        }
    except Exception as e:
        return {"hits": 0, "malicious": False, "tags": [], "error": str(e)}


def create_iris_case(title: str, description: str, severity: int = 3, token: str = "") -> str:
    """Create a structured incident case in DFIR-IRIS."""
    auth_token = token or os.getenv("IRIS_TOKEN", "")
    if not auth_token:
        return "N/A (No IRIS token)"

    session = requests.Session()
    session.verify = False
    try:
        r = session.post(
            f"{IRIS_URL}/api/v1/cases/add",
            headers={**DEFAULT_HEADERS, "Authorization": f"Bearer {auth_token}"},
            json={
                "case_name": f"[AUTO] {title}",
                "case_description": description,
                "case_severity_id": severity,
                "case_customer": 1
            },
            timeout=15
        )
        return r.json().get("data", {}).get("case_id", "N/A")
    except Exception as e:
        return f"ERROR: {e}"
