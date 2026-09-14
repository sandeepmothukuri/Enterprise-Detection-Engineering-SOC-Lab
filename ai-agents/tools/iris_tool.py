"""DFIR-IRIS tools for case, evidence, IOC and timeline management."""
import json
import os

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


def _iris_base() -> str:
    return os.getenv("IRIS_URL", "https://dfir-iris:443").rstrip("/")


def _iris_verify():
    ca = os.getenv("IRIS_CA_CERT", "/etc/iris/iris-ca.pem")
    if not os.path.isfile(ca):
        raise RuntimeError(f"DFIR-IRIS CA certificate is missing: {ca}")
    return ca


def _iris_headers() -> dict[str, str]:
    key = os.getenv("IRIS_ADM_API_KEY", "")
    if not key:
        raise RuntimeError("IRIS_ADM_API_KEY is not configured")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


class IRISCreateCaseInput(BaseModel):
    title: str = Field(...)
    description: str = Field(...)
    severity: int = Field(default=3, description="1=Informational through 5=Critical")
    owner: str = Field(default="SOC-AI-Agent")
    tags: list[str] = Field(default_factory=list)


class IRISCreateCaseTool(BaseTool):
    name: str = "iris_create_case"
    description: str = "Create a DFIR-IRIS incident case for a confirmed investigation."
    args_schema: type[BaseModel] = IRISCreateCaseInput

    def _run(self, title: str, description: str, severity: int = 3,
             owner: str = "SOC-AI-Agent", tags: list[str] | None = None) -> str:
        payload = {
            "case_name": title,
            "case_description": description,
            "case_customer": 1,
            "case_severity_id": severity,
            "case_classification_id": 1,
            "custom_attributes": {"owner": owner, "tags": tags or []},
        }
        try:
            response = requests.post(
                f"{_iris_base()}/api/v1/cases/add",
                json=payload,
                headers=_iris_headers(),
                verify=_iris_verify(),
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            case_id = data.get("data", {}).get("case_id")
            return json.dumps({"status": "created", "case_id": case_id,
                               "url": f"{_iris_base()}/case?cid={case_id}"})
        except Exception as exc:
            return json.dumps({"error": str(exc)})


class IRISAddEvidenceInput(BaseModel):
    case_id: int = Field(...)
    filename: str = Field(...)
    description: str = Field(...)
    ioc_value: str = Field(default="")
    ioc_type: str = Field(default="")


class IRISAddEvidenceTool(BaseTool):
    name: str = "iris_add_evidence"
    description: str = "Add forensic evidence and, when supplied, an IOC to an IRIS case."
    args_schema: type[BaseModel] = IRISAddEvidenceInput

    def _run(self, case_id: int, filename: str, description: str,
             ioc_value: str = "", ioc_type: str = "") -> str:
        try:
            note_payload = {
                "note_title": filename,
                "note_content": description,
                "custom_attributes": {},
                "cid": case_id,
            }
            response = requests.post(
                f"{_iris_base()}/api/v1/case/notes/add",
                json=note_payload,
                headers=_iris_headers(),
                params={"cid": case_id},
                verify=_iris_verify(),
                timeout=15,
            )
            response.raise_for_status()
            result = {"evidence_added": filename, "case_id": case_id}
            if ioc_value and ioc_type:
                ioc_payload = {
                    "ioc_value": ioc_value,
                    "ioc_type_id": {"ip": 76, "domain": 6, "md5": 23, "sha256": 24}.get(ioc_type, 1),
                    "ioc_tlp_id": 2,
                    "ioc_description": description,
                    "custom_attributes": {},
                    "cid": case_id,
                }
                ioc_response = requests.post(
                    f"{_iris_base()}/api/v1/case/ioc/add",
                    json=ioc_payload,
                    headers=_iris_headers(),
                    params={"cid": case_id},
                    verify=_iris_verify(),
                    timeout=15,
                )
                ioc_response.raise_for_status()
                result["ioc_added"] = ioc_value
            return json.dumps(result)
        except Exception as exc:
            return json.dumps({"error": str(exc)})


class IRISTimelineInput(BaseModel):
    case_id: int = Field(...)
    title: str = Field(...)
    content: str = Field(...)
    start_time: str = Field(...)
    category: str = Field(default="Network")


class IRISAddTimelineTool(BaseTool):
    name: str = "iris_add_timeline"
    description: str = "Add a timeline event to a DFIR-IRIS investigation case."
    args_schema: type[BaseModel] = IRISTimelineInput

    def _run(self, case_id: int, title: str, content: str,
             start_time: str, category: str = "Network") -> str:
        payload = {
            "title": title,
            "content": content,
            "raw_data": "",
            "start_date": start_time,
            "parent_id": None,
            "cid": case_id,
            "category": category,
        }
        try:
            response = requests.post(
                f"{_iris_base()}/api/v1/case/timeline/events/add",
                json=payload,
                headers=_iris_headers(),
                params={"cid": case_id},
                verify=_iris_verify(),
                timeout=15,
            )
            response.raise_for_status()
            return json.dumps({"status": "timeline_event_added", "case_id": case_id, "title": title})
        except Exception as exc:
            return json.dumps({"error": str(exc)})
