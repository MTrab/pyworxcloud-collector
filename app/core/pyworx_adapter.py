
import asyncio
from pyworxcloud import WorxCloud

class PyWorxSession:
    def __init__(self, email, password, collector):
        self.email = email
        self.password = password
        self.collector = collector
        self.client = None
        self._task = None
        self._running = False

    async def start(self):
        self.client = WorxCloud(self.email, self.password)
        await self.client.login()
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())

    async def _poll_loop(self):
        while self._running:
            try:
                mowers = await self.client.get_mowers()
                for mower in mowers:
                    status = await mower.get_status()
                    self.collector.record_http({
                        "mower_id": mower.id,
                        "status": status,
                    })
            except Exception as e:
                self.collector.record_http({
                    "error": str(e),
                    "exception_type": type(e).__name__,
                })
            await asyncio.sleep(30)

    async def stop(self):
        self._running = False
        if self._task:
            await self._task
