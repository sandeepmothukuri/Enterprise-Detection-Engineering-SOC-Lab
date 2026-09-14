"""
OpenSearch Tool — query the SOC SIEM for alerts, events, Zeek logs,
Suricata alerts, Windows events and audit data.
"""
from datetime import datetime, timedelta, timezone
import json
import os

from crewai.tools import BaseTool
from opensearchpy import OpenSearch
from pydantic import BaseModel, Field


def _client() -> OpenSearch:
    host = os.getenv("OPENSEARCH_HOST", "opensearch-node1")
    port = int(os.getenv("OPENSEARCH_PORT", "9200"))
    user = os.getenv("OPENSEARCH_USER", "admin")
    password = os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD", "")
    ca_cert = os.getenv("OPENSEARCH_CA_CERT", "/etc/opensearch/root-ca.pem")

    if not password:
        raise RuntimeError("OPENSEARCH_INITIAL_ADMIN_PASSWORD is not configured")

    return OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(user, password),
        use_ssl=True,
        verify_certs=True,
        ca_certs=ca_cert,
        ssl_show_warn=False,
    )


class OpenSearchQueryInput(BaseModel):
    query: str = Field(..., description="Lucene query string")
    index: str = Field(default="soc-logs-*", description="Index pattern to search")
    hours_back: int = Field(default=24, description="Look-back window in hours")
    size: int = Field(default=20, description="Maximum number of results")


class OpenSearchTool(BaseTool):
    name: str = "opensearch_query"
    description: str = (
        "Search the SOC SIEM for security alerts, events, Zeek logs, Suricata alerts, "
        "Windows Sysmon events, audit logs and MITRE ATT&CK context."
    )
    args_schema: type[BaseModel] = OpenSearchQueryInput

    def _run(self, query: str, index: str = "soc-logs-*", hours_back: int = 24, size: int = 20) -> str:
        since = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()
        body = {
            "query": {
                "bool": {
                    "must": [{"query_string": {"query": query}}],
                    "filter": [{"range": {"@timestamp": {"gte": since}}}],
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": size,
        }
        try:
            resp = _client().search(index=index, body=body)
            hits = resp["hits"]["hits"]
            results = []
            for hit in hits:
                src = hit.get("_source", {})
                results.append({
                    "timestamp": src.get("@timestamp"),
                    "mitre_tactic": src.get("mitre_tactic"),
                    "mitre_technique": src.get("mitre_technique"),
                    "event_type": src.get("event_type"),
                    "source_ip": src.get("src_ip") or src.get("source", {}).get("ip"),
                    "dest_ip": src.get("dst_ip") or src.get("destination", {}).get("ip"),
                    "hostname": src.get("hostname") or src.get("host", {}).get("name"),
                    "process": src.get("process", {}).get("name") or src.get("Image"),
                    "message": src.get("message") or src.get("alert", {}).get("signature"),
                    "severity": src.get("severity") or src.get("alert", {}).get("severity"),
                })
            return json.dumps({
                "total_hits": resp["hits"]["total"]["value"],
                "returned": len(results),
                "query": query,
                "window_hours": hours_back,
                "results": results,
            }, indent=2)
        except Exception as exc:
            return json.dumps({"error": str(exc), "query": query})


class OpenSearchStatsInput(BaseModel):
    hours_back: int = Field(default=1, description="Stats window in hours")


class OpenSearchStatsTool(BaseTool):
    name: str = "opensearch_stats"
    description: str = (
        "Get real-time SOC statistics: event counts by severity, source IP, "
        "MITRE technique and sensor in the last N hours."
    )
    args_schema: type[BaseModel] = OpenSearchStatsInput

    def _run(self, hours_back: int = 1) -> str:
        since = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()
        body = {
            "query": {"range": {"@timestamp": {"gte": since}}},
            "aggs": {
                "by_severity": {"terms": {"field": "severity", "size": 5}},
                "by_mitre": {"terms": {"field": "mitre_technique", "size": 10}},
                "by_src_ip": {"terms": {"field": "src_ip", "size": 10}},
                "by_sensor": {"terms": {"field": "sensor", "size": 5}},
            },
            "size": 0,
        }
        try:
            resp = _client().search(index="soc-logs-*", body=body)
            aggs = resp.get("aggregations", {})
            return json.dumps({
                "total_events": resp["hits"]["total"]["value"],
                "window_hours": hours_back,
                "by_severity": {b["key"]: b["doc_count"] for b in aggs.get("by_severity", {}).get("buckets", [])},
                "top_mitre_techniques": {b["key"]: b["doc_count"] for b in aggs.get("by_mitre", {}).get("buckets", [])},
                "top_source_ips": {b["key"]: b["doc_count"] for b in aggs.get("by_src_ip", {}).get("buckets", [])},
                "by_sensor": {b["key"]: b["doc_count"] for b in aggs.get("by_sensor", {}).get("buckets", [])},
            }, indent=2)
        except Exception as exc:
            return json.dumps({"error": str(exc)})
