"""
FastAPI endpoint — receives webhook alerts from ElastAlert2/StackStorm
and dispatches them to the appropriate CrewAI SOC mission.
"""
import os
import sqlite3
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from ai_agents.crews import run_mission
except ImportError:
    try:
        from crews.soc_crew import run_mission
    except ImportError:
        def run_mission(mission: str, context: dict, hypothesis: str = "") -> str:
            return f"[SIMULATED_AI_REPORT] Completed {mission} analysis for context: {json.dumps(context)}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("soc_ai_api")

app = FastAPI(
    title="SOC AI Agent API",
    description="CrewAI-powered autonomous SOC agents for threat analysis, incident response, and threat hunting",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("AI_JOBS_DB", "soc_ai_jobs.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            mission TEXT,
            status TEXT,
            context TEXT,
            result TEXT,
            error TEXT,
            queued_at TEXT,
            started_at TEXT,
            completed_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


def save_job(job_id: str, mission: str, status: str, context: dict = None, result: str = "", error: str = "", started_at: str = "", completed_at: str = ""):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO jobs (job_id, mission, status, context, result, error, queued_at, started_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT queued_at FROM jobs WHERE job_id = ?), ?), ?, ?)
    """, (
        job_id, mission, status,
        json.dumps(context or {}),
        result, error,
        job_id, datetime.utcnow().isoformat(),
        started_at, completed_at
    ))
    conn.commit()
    conn.close()


def load_job(job_id: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT job_id, mission, status, context, result, error, queued_at, started_at, completed_at FROM jobs WHERE job_id = ?", (job_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "job_id": row[0],
        "mission": row[1],
        "status": row[2],
        "context": json.loads(row[3]) if row[3] else {},
        "result": row[4],
        "error": row[5],
        "queued_at": row[6],
        "started_at": row[7],
        "completed_at": row[8]
    }


class AlertRequest(BaseModel):
    alert_type: str
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    hostname: Optional[str] = None
    mitre_technique: Optional[str] = None
    severity: Optional[str] = "medium"
    raw_alert: Optional[Dict[str, Any]] = {}
    mission: Optional[str] = "alert_triage"  # alert_triage | incident_response | full_soc


class HuntRequest(BaseModel):
    hypothesis: str
    target_hosts: Optional[list] = []
    time_window_hours: Optional[int] = 24
    tactic_focus: Optional[str] = "all"


class DetectionRequest(BaseModel):
    tactic: Optional[str] = "all"
    recent_incident: Optional[str] = ""


def _run_mission_bg(job_id: str, mission: str, context: dict, hypothesis: str = ""):
    """Background task runner with SQLite persistence and error trapping."""
    started_at = datetime.utcnow().isoformat()
    save_job(job_id, mission, status="running", context=context, started_at=started_at)
    try:
        result = run_mission(mission, context, hypothesis)
        completed_at = datetime.utcnow().isoformat()
        save_job(job_id, mission, status="completed", context=context, result=str(result), started_at=started_at, completed_at=completed_at)
    except Exception as e:
        logger.exception(f"Mission {mission} failed for job {job_id}")
        save_job(job_id, mission, status="failed", context=context, error=str(e), started_at=started_at, completed_at=datetime.utcnow().isoformat())


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "agents": 4,
        "version": "2.1.0",
        "persistence": "sqlite",
        "ollama_url": os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        "model": os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    }


@app.post("/analyze/alert")
async def analyze_alert(req: AlertRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    context = {
        "alert_type": req.alert_type,
        "source_ip": req.source_ip,
        "dest_ip": req.dest_ip,
        "hostname": req.hostname,
        "mitre_technique": req.mitre_technique,
        "severity": req.severity,
        **req.raw_alert,
    }
    save_job(job_id, req.mission, status="queued", context=context)
    background_tasks.add_task(_run_mission_bg, job_id, req.mission, context)
    return {
        "job_id": job_id,
        "mission": req.mission,
        "status": "queued",
        "poll_url": f"/jobs/{job_id}"
    }


@app.post("/hunt")
async def start_hunt(req: HuntRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    context = {
        "target_hosts": req.target_hosts,
        "time_window_hours": req.time_window_hours,
        "tactic_focus": req.tactic_focus,
    }
    save_job(job_id, "threat_hunt", status="queued", context=context)
    background_tasks.add_task(_run_mission_bg, job_id, "threat_hunt", context, req.hypothesis)
    return {"job_id": job_id, "hypothesis": req.hypothesis, "status": "queued"}


@app.post("/detection/gaps")
async def detection_gaps(req: DetectionRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    context = {"tactic": req.tactic, "recent_incident": req.recent_incident}
    save_job(job_id, "detection_gap", status="queued", context=context)
    background_tasks.add_task(_run_mission_bg, job_id, "detection_gap", context)
    return {"job_id": job_id, "tactic": req.tactic, "status": "queued"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/jobs")
def list_jobs():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT job_id, mission, status, queued_at, completed_at FROM jobs ORDER BY queued_at DESC LIMIT 50")
    rows = cur.fetchall()
    conn.close()
    return {
        "total": len(rows),
        "jobs": [{
            "id": r[0],
            "mission": r[1],
            "status": r[2],
            "queued_at": r[3],
            "completed_at": r[4]
        } for r in rows],
    }


@app.post("/webhook/elastalert")
async def elastalert_webhook(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    rule_name = payload.get("rule_name", "unknown")
    severity = payload.get("severity", "medium")
    mission = "full_soc" if severity in ("critical", "high") else "alert_triage"

    job_id = str(uuid.uuid4())[:8]
    save_job(job_id, mission, status="queued", context=payload)
    background_tasks.add_task(_run_mission_bg, job_id, mission, payload)
    logger.info(f"ElastAlert2 webhook received: rule={rule_name} mission={mission} job={job_id}")
    return {"received": True, "job_id": job_id, "mission": mission}
