
from fastapi import APIRouter, HTTPException
from uuid import uuid4
from datetime import datetime, timedelta
from pathlib import Path
from app.core.collector import CollectorSink
from app.core.pyworx_adapter import PyWorxSession
from app.storage.store import export_zip
import asyncio

router = APIRouter()
BASE = Path("/data/sessions")
SESSIONS = {}

@router.post("/login")
async def login(email: str, password: str, consent: bool):
    if not consent:
        raise HTTPException(400, "Consent required")
    return {"status": "ok"}

@router.post("/sessions/start")
async def start_session(email: str, password: str, hours: int = 2):
    sid = str(uuid4())
    session_dir = BASE / sid
    collector = CollectorSink(session_dir)
    adapter = PyWorxSession(email, password, collector)

    await adapter.start()

    expires = datetime.utcnow() + timedelta(hours=hours)
    SESSIONS[sid] = {
        "adapter": adapter,
        "collector": collector,
        "dir": session_dir,
        "expires": expires,
        "active": True,
    }
    return {"session_id": sid, "expires": expires.isoformat()}

@router.post("/sessions/{sid}/stop")
async def stop_session(sid: str):
    s = SESSIONS.get(sid)
    if not s:
        raise HTTPException(404)
    await s["adapter"].stop()
    s["collector"].flush()
    s["active"] = False
    return {"status": "stopped"}

@router.get("/sessions/{sid}/download")
async def download(sid: str):
    s = SESSIONS.get(sid)
    if not s:
        raise HTTPException(404)
    out = s["dir"] / "export.zip"
    export_zip(s["dir"], out)
    return {"zip_path": str(out)}
