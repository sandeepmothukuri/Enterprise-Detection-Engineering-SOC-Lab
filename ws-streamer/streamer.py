#!/usr/bin/env python3
"""Real-time WebSocket alert streamer backed by OpenSearch."""
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone

import websockets
from opensearchpy import OpenSearch, OpenSearchException

logging.basicConfig(level=logging.INFO, format="%(asctime)s [WS-STREAMER] %(levelname)s — %(message)s")
log = logging.getLogger(__name__)

OS_HOST = os.getenv("OPENSEARCH_HOST", "opensearch-node1")
OS_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
OS_USER = os.getenv("OPENSEARCH_USER", "admin")
OS_PASS = os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD", "")
OS_CA = os.getenv("OPENSEARCH_CA_CERT", "/etc/opensearch/root-ca.pem")
WS_HOST = os.getenv("WS_HOST", "0.0.0.0")
WS_PORT = int(os.getenv("WS_PORT", "8765"))
POLL_SECS = int(os.getenv("POLL_INTERVAL_SECS", "5"))
CLIENTS: set = set()
last_seen_ts: str = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()


def get_os_client() -> OpenSearch:
    if not OS_PASS:
        raise RuntimeError("OPENSEARCH_INITIAL_ADMIN_PASSWORD is not configured")
    return OpenSearch(
        hosts=[{"host": OS_HOST, "port": OS_PORT}],
        http_auth=(OS_USER, OS_PASS),
        use_ssl=True,
        verify_certs=True,
        ca_certs=OS_CA,
        ssl_show_warn=False,
        retry_on_timeout=True,
    )


def fetch_new_alerts(client: OpenSearch) -> list[dict]:
    global last_seen_ts
    body = {
        "query": {
            "bool": {
                "filter": [{"range": {"@timestamp": {"gt": last_seen_ts}}}],
                "should": [
                    {"exists": {"field": "mitre_technique"}},
                    {"term": {"event_type": "alert"}},
                    {"term": {"log_type": "suricata"}},
                ],
                "minimum_should_match": 1,
            }
        },
        "sort": [{"@timestamp": {"order": "asc"}}],
        "size": 50,
    }
    try:
        hits = client.search(index="soc-logs-*", body=body)["hits"]["hits"]
        alerts = []
        for hit in hits:
            src = hit.get("_source", {})
            alerts.append({
                "id": hit["_id"],
                "timestamp": src.get("@timestamp"),
                "type": src.get("event_type") or src.get("log_type") or "event",
                "mitre_tactic": src.get("mitre_tactic", ""),
                "mitre_technique": src.get("mitre_technique", ""),
                "severity": src.get("severity") or (src.get("alert") or {}).get("severity", "medium"),
                "src_ip": src.get("src_ip") or (src.get("source") or {}).get("ip", ""),
                "dest_ip": src.get("dst_ip") or (src.get("destination") or {}).get("ip", ""),
                "hostname": src.get("hostname") or (src.get("host") or {}).get("name", ""),
                "message": src.get("message") or (src.get("alert") or {}).get("signature", ""),
                "sensor": src.get("sensor", "unknown"),
            })
        if alerts:
            last_seen_ts = alerts[-1]["timestamp"]
        return alerts
    except OpenSearchException as exc:
        log.warning("OpenSearch poll error: %s", exc)
        return []


async def broadcast(message: str):
    if not CLIENTS:
        return
    dead = set()
    for ws in CLIENTS.copy():
        try:
            await ws.send(message)
        except websockets.exceptions.ConnectionClosed:
            dead.add(ws)
    CLIENTS.difference_update(dead)


async def poll_loop():
    client = None
    while True:
        await asyncio.sleep(POLL_SECS)
        try:
            client = client or get_os_client()
            alerts = fetch_new_alerts(client)
            if alerts:
                await broadcast(json.dumps({
                    "type": "alerts",
                    "count": len(alerts),
                    "alerts": alerts,
                    "server_time": datetime.now(timezone.utc).isoformat(),
                }))
        except Exception as exc:
            log.error("Poll loop error: %s", exc)
            client = None


async def heartbeat_loop():
    while True:
        await asyncio.sleep(30)
        await broadcast(json.dumps({
            "type": "heartbeat",
            "server_time": datetime.now(timezone.utc).isoformat(),
            "connected_clients": len(CLIENTS),
        }))


async def handler(websocket):
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    CLIENTS.add(websocket)
    log.info("Client connected: %s", client_ip)
    try:
        response = get_os_client().count(index="soc-logs-*", body={
            "query": {"range": {"@timestamp": {"gte": "now-1h"}}}
        })
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to SOC Alert Stream",
            "events_last_1h": response.get("count", 0),
            "server_time": datetime.now(timezone.utc).isoformat(),
        }))
    except Exception as exc:
        log.warning("Welcome query failed: %s", exc)
    try:
        async for _ in websocket:
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CLIENTS.discard(websocket)
        log.info("Client disconnected: %s", client_ip)


async def main():
    log.info("SOC WebSocket Streamer starting on %s:%s", WS_HOST, WS_PORT)
    async with websockets.serve(handler, WS_HOST, WS_PORT):
        await asyncio.gather(poll_loop(), heartbeat_loop())


if __name__ == "__main__":
    asyncio.run(main())
