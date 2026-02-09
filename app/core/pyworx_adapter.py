
import threading
import time
from datetime import datetime
from pyworxcloud import WorxCloud
from pyworxcloud.clouds import CloudType


class PyWorxSession:
    def __init__(self, username: str, password: str, brand: str, collector, interval: int = 30):
        self.username = username
        self.password = password
        self.brand = brand
        self.collector = collector
        self.interval = interval
        self.cloud = None
        self._thread = None
        self._running = False

    def _cloud_type(self) -> CloudType:
        return {
            "worx": CloudType.WORX,
            "kress": CloudType.KRESS,
            "landxcape": CloudType.LANDXCAPE,
        }[self.brand]

    def start(self):
        self.cloud = WorxCloud(
            self.username,
            self.password,
            self._cloud_type(),
            tz="Europe/Copenhagen",
        )

        self.cloud.authenticate()
        self.cloud.connect()

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
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

            time.sleep(self.interval)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self.cloud:
            self.cloud.disconnect()
