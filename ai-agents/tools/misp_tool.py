"""MISP threat-intelligence tools for IOC enrichment and event creation."""
import json
import os

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


def _misp_base() -> str:
    return os.getenv("MISP_URL", "http://misp:80").rstrip("/")


def _misp_headers() -> dict[str, str]:
    key = os.getenv("MISP_API_KEY", "")
    if not key:
        raise RuntimeError("MISP_API_KEY is not configured")
    return {"Authorization": key, "Accept": "application/json", "Content-Type": "application/json"}


class MISPSearchInput(BaseModel):
    value: str = Field(...)
    ioc_type: str = Field(default="auto")


class MISPSearchTool(BaseTool):
    name: str = "misp_search_ioc"
    description: str = "Search MISP for an IOC and return matching threat-intelligence context."
    args_schema: type[BaseModel] = MISPSearchInput

    def _run(self, value: str, ioc_type: str = "auto") -> str:
        payload = {"returnFormat": "json", "value": value, "limit": 20, "includeEventTags": True}
        if ioc_type != "auto":
            payload["type"] = ioc_type
        try:
            response = requests.post(
                f"{_misp_base()}/attributes/restSearch",
                json=payload,
                headers=_misp_headers(),
                timeout=15,
            )
            response.raise_for_status()
            attrs = response.json().get("response", {}).get("Attribute", [])
            results = [{
                "event_id": item.get("event_id"),
                "type": item.get("type"),
                "value": item.get("value"),
                "category": item.get("category"),
                "to_ids": item.get("to_ids"),
                "tags": [tag.get("name") for tag in item.get("Tag", [])],
                "timestamp": item.get("timestamp"),
            } for item in attrs]
            return json.dumps({
                "ioc": value,
                "matches": len(results),
                "threat_intel": results,
                "verdict": "MALICIOUS" if results else "UNKNOWN",
            }, indent=2)
        except Exception as exc:
            return json.dumps({"error": str(exc), "ioc": value})


class MISPCreateEventInput(BaseModel):
    title: str = Field(...)
    iocs: list[str] = Field(...)
    threat_level: int = Field(default=2)
    tags: list[str] = Field(default_factory=list)


class MISPCreateEventTool(BaseTool):
    name: str = "misp_create_event"
    description: str = "Create a MISP threat-intelligence event from analyst-approved IOCs."
    args_schema: type[BaseModel] = MISPCreateEventInput

    def _run(self, title: str, iocs: list[str], threat_level: int = 2,
             tags: list[str] | None = None) -> str:
        event_payload = {
            "Event": {
                "info": title,
                "threat_level_id": str(threat_level),
                "analysis": "1",
                "distribution": "0",
                "Tag": [{"name": tag} for tag in (tags or [])],
                "Attribute": [
                    {"type": "text", "value": ioc, "category": "External analysis"}
                    for ioc in iocs
                ],
            }
        }
        try:
            response = requests.post(
                f"{_misp_base()}/events/add",
                json=event_payload,
                headers=_misp_headers(),
                timeout=15,
            )
            response.raise_for_status()
            event = response.json().get("Event", {})
            return json.dumps({"status": "created", "event_id": event.get("id"), "uuid": event.get("uuid")})
        except Exception as exc:
            return json.dumps({"error": str(exc)})
