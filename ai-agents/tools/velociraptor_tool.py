"""Velociraptor tools for analyst-approved endpoint forensics."""
import json
import os
from pathlib import Path

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


def _vr_base() -> str:
    return os.getenv("VELOCIRAPTOR_URL", "https://velociraptor:8000").rstrip("/")


def _vr_verify():
    ca = os.getenv("VELOCIRAPTOR_CA_CERT", "/etc/iris/velociraptor-ca.pem")
    if not Path(ca).is_file():
        raise RuntimeError(f"Velociraptor trust chain is missing: {ca}")
    return ca


def _vr_headers() -> dict[str, str]:
    key = os.getenv("VELOCIRAPTOR_API_KEY", "")
    if not key:
        raise RuntimeError("VELOCIRAPTOR_API_KEY is not configured")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


HUNT_ARTIFACTS = {
    "process_list": "Windows.System.Pslist",
    "network": "Windows.Network.NetstatEnriched",
    "evidence": "Windows.Analysis.EvidenceOf.Execution",
    "prefetch": "Windows.Forensics.Prefetch",
    "scheduled_tasks": "Windows.System.ScheduledTasks",
    "services": "Windows.System.Services",
    "registry_run": "Windows.Registry.Sysinternals.Autoruns",
    "yara_memory": "Windows.Memory.Acquisition",
    "browser_history": "Windows.Forensics.BrowserHistory",
    "usb_history": "Windows.Forensics.USB",
    "event_logs": "Windows.EventLogs.Evtx",
    "lsass_handles": "Windows.System.HandleDuplication",
    "dns_cache": "Windows.Network.DNS",
    "linux_processes": "Linux.Sys.Pslist",
    "linux_network": "Linux.Network.Netstat",
    "linux_bash": "Linux.Sys.BashHistory",
    "linux_cron": "Linux.Sys.Crontab",
}


class VelociraptorHuntInput(BaseModel):
    hostname: str = Field(...)
    artifact: str = Field(...)
    parameters: dict = Field(default_factory=dict)


class VelociraptorHuntTool(BaseTool):
    name: str = "velociraptor_hunt"
    description: str = "Launch an authenticated Velociraptor forensic hunt on an endpoint."
    args_schema: type[BaseModel] = VelociraptorHuntInput

    def _run(self, hostname: str, artifact: str, parameters: dict | None = None) -> str:
        artifact_name = HUNT_ARTIFACTS.get(artifact, artifact)
        payload = {
            "artifacts": [artifact_name],
            "condition": f"Host.Fqdn =~ '{hostname}'",
            "parameters": {"env": [{"key": k, "value": v} for k, v in (parameters or {}).items()]},
        }
        try:
            response = requests.post(
                f"{_vr_base()}/api/v1/CreateHunt",
                json=payload,
                headers=_vr_headers(),
                verify=_vr_verify(),
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            hunt_id = data.get("hunt_id", "unknown")
            return json.dumps({
                "status": "hunt_launched",
                "hunt_id": hunt_id,
                "artifact": artifact_name,
                "target": hostname,
                "collect_url": f"{_vr_base()}/app/hunts/{hunt_id}",
            })
        except Exception as exc:
            return json.dumps({"error": str(exc), "artifact": artifact_name, "target": hostname})


class VelociraptorQueryInput(BaseModel):
    vql: str = Field(...)
    client_id: str = Field(default="")


class VelociraptorVQLTool(BaseTool):
    name: str = "velociraptor_vql"
    description: str = "Execute authenticated Velociraptor VQL for hypothesis-driven forensic investigation."
    args_schema: type[BaseModel] = VelociraptorQueryInput

    def _run(self, vql: str, client_id: str = "") -> str:
        payload = {"query": [{"vql": vql}]}
        if client_id:
            payload["client_id"] = client_id
        try:
            response = requests.post(
                f"{_vr_base()}/api/v1/Query",
                json=payload,
                headers=_vr_headers(),
                verify=_vr_verify(),
                timeout=20,
            )
            response.raise_for_status()
            return json.dumps(response.json())
        except Exception as exc:
            return json.dumps({"error": str(exc), "vql": vql})
