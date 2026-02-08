
from fastapi import APIRouter, HTTPException
from uuid import uuid4
from datetime import datetime, timedelta
from pathlib import Path
from app.core.collector import CollectorSink
from app.storage.store import export_zip

router = APIRouter()
BASE = Path("/tmp/collector")
SESSIONS = {}

@router.post("/login")
def login(email: str, password: str, consent: bool):
    if not consent:
        raise HTTPException(400, "Consent required")
    # Credentials are intentionally not stored
    return {"status": "ok", "note": "Credentials kept in memory only"}

@router.post("/sessions/start")
def start_session(hours: int = 2):
    sid = str(uuid4())
    expires = datetime.utcnow() + timedelta(hours=hours)
    session_dir = BASE / sid
    collector = CollectorSink(session_dir)

    SESSIONS[sid] = {
        "started": datetime.utcnow().isoformat(),
        "expires": expires.isoformat(),
        "active": True,
        "collector": collector,
        "dir": session_dir,
    }
    return {"session_id": sid, "expires": expires}

@router.get("/sessions/{sid}")
def session_info(sid: str):
    s = SESSIONS.get(sid)
    if not s:
        raise HTTPException(404)
    return {
        "started": s["started"],
        "expires": s["expires"],
        "active": s["active"],
        "summary": s["collector"].summary(),
    }

@router.post("/sessions/{sid}/stop")
def stop_session(sid: str):
    s = SESSIONS.get(sid)
    if not s:
        raise HTTPException(404)
    s["active"] = False
    s["collector"].dump()
    return {"status": "stopped"}

@router.get("/sessions/{sid}/download")
def download(sid: str):
    s = SESSIONS.get(sid)
    if not s:
        raise HTTPException(404)
    out = s["dir"] / "export.zip"
    export_zip(s["dir"], out)
    return {"zip": str(out)}
