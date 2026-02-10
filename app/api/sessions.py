
import os
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.collector import Collector
from app.core.pyworx_adapter import PyWorxAdapterError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions")
collector = Collector()

class StartRequest(BaseModel):
    username: str
    password: str
    brand: str
    consent: bool

@router.post("/start")
def start(payload: StartRequest):
    if not payload.consent:
        raise HTTPException(status_code=400, detail="Consent is required to start.")
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")
    brand = (payload.brand or "").lower()
    if brand not in {"worx", "kress", "landxcape"}:
        raise HTTPException(status_code=400, detail="Invalid brand.")
    try:
        return collector.start(payload.username, payload.password, brand)
    except PyWorxAdapterError as exc:
        logger.error("PyWorxAdapterError on start: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/{sid}/stop")
def stop(sid: str):
    res = collector.stop(sid)
    if not res:
        raise HTTPException(status_code=404, detail="Session not found.")
    return res

@router.get("/{sid}/download")
def download(sid: str, background_tasks: BackgroundTasks):
    zip_path = collector.build_zip(sid)
    if not zip_path:
        raise HTTPException(status_code=404, detail="No data available for download.")
    background_tasks.add_task(os.remove, zip_path)
    return FileResponse(zip_path, media_type="application/zip", filename=f"{sid}.zip")
