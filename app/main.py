
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.sessions import router as session_router

app = FastAPI(title="pyworxcloud Collector")

app.include_router(session_router, prefix="/api")
app.mount("/", StaticFiles(directory="app/ui", html=True), name="ui")
