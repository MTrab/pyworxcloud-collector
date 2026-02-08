
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.sessions import router

app = FastAPI(title="pyworxcloud Collector")
app.include_router(router, prefix="/api")
app.mount("/", StaticFiles(directory="app/ui", html=True), name="ui")
