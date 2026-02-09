
import asyncio
from datetime import datetime
from pyworxcloud import WorxCloud
from pyworxcloud.clouds import CloudType


class PyWorxSession:
    def __init__(self, username: str, password: str, brand: str, collector):
        self.username = username
        self.password = password
        self.brand = brand
        self.collector = collector
        self.cloud: WorxCloud | None = None
        self._running = False
        self._task: asyncio.Task | None = None

    def _cloud_type(self) -> CloudType:
        mapping = {
            "worx": CloudType.WORX,
            "kress": CloudType.KRESS,
            "landxcape": CloudType.LANDXCAPE,
        }
        return mapping[self.brand]

    async def start(self) -> None:
        self.cloud = WorxCloud(
            self.username,
            self.password,
            self._cloud_type(),
        )

        await self.cloud.authenticate()
        await self.cloud.connect()

        self._running = True
        self._task = asyncio.create_task(self._collect_loop())

    async def _collect_loop(self) -> None:
        assert self.cloud is not None

        while self._running:
            try:
                for _, device in self.cloud.devices.items():
                    self.cloud.update(device.serial_number)
                    self.collector.record_http({
                        "timestamp": datetime.utcnow().isoformat(),
                        "serial_number": device.serial_number,
                        "device": vars(device),
                    })
            except Exception as exc:
                self.collector.record_http({
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(exc),
                    "exception_type": type(exc).__name__,
                })

            await asyncio.sleep(30)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            await self._task
