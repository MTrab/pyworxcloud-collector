
import os
import tempfile
import uuid
import zipfile

from app.core.pyworx_adapter import PyWorxAdapter, PyWorxAdapterError


class Collector:
    def __init__(self):
        self.sessions = {}

    async def start(self, username, password, brand):
        sid = str(uuid.uuid4())
        adapter = PyWorxAdapter(sid, username, password, brand)
        try:
            await adapter.start()
        except PyWorxAdapterError:
            raise
        self.sessions[sid] = adapter
        # include devices metadata (name/model/serial) for API consumers
        devices = getattr(adapter, "devices_info", [])
        return {"session": sid, "devices": devices}

    async def stop(self, sid):
        if sid in self.sessions:
            adapter = self.sessions[sid]
            try:
                await adapter.stop()
            except Exception:
                pass
            del self.sessions[sid]
            return {"stopped": sid}
        return None

    def status(self, sid):
        path = f"/app/data/{sid}"
        return {"files": os.listdir(path) if os.path.exists(path) else []}

    def build_zip(self, sid):
        path = f"/app/data/{sid}"
        if not os.path.exists(path):
            return None

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"-{sid}.zip")
        tmp.close()

        with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(path):
                for name in files:
                    full = os.path.join(root, name)
                    rel = os.path.relpath(full, path)
                    zf.write(full, rel)

        return tmp.name
