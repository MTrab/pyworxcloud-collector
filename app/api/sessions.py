
from fastapi import APIRouter, HTTPException
from uuid import uuid4
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel
from app.core.collector import CollectorSink
from app.core.pyworx_adapter import PyWorxSession
from app.storage.store import export_zip

router = APIRouter()
BASE = Path("/data/sessions")
SESSIONS = {}

class StartSessionRequest(BaseModel):
    email: str
    password: str
    brand: str
    hours: int = 2

@router.post("/sessions/start")
async def start_session(req: StartSessionRequest):
    sid = str(uuid4())
    session_dir = BASE / sid
    collector = CollectorSink(session_dir)
    adapter = PyWorxSession(
        email=req.email,
        password=req.password,
        brand=req.brand,
        collector=collector
    )
    await adapter.start()

    expires = datetime.utcnow() + timedelta(hours=req.hours)
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
