
import threading
import time
from datetime import datetime
from pyworxcloud import WorxCloud
from pyworxcloud.clouds import CloudType
from pyworxcloud.events import LandroidEvent


class PyWorxSession:
    def __init__(self, username: str, password: str, brand: str, collector, interval: int = 60):
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

        self.cloud.set_callback(LandroidEvent.DATA_RECEIVED, self._on_mqtt)
        self.cloud.set_callback(LandroidEvent.API, self._on_http)

        self.cloud.authenticate()
        self.cloud.connect()

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _on_mqtt(self, serial_number: str, payload: dict):
        self.collector.record_mqtt({
            "timestamp": datetime.utcnow().isoformat(),
            "serial_number": serial_number,
            "payload": payload,
        })

    def _on_http(self, serial_number: str, payload: dict):
        self.collector.record_http({
            "timestamp": datetime.utcnow().isoformat(),
            "serial_number": serial_number,
            "payload": payload,
        })

    def _loop(self):
        while self._running:
            for serial in list(self.cloud.devices.keys()):
                self.cloud.update(serial)
            time.sleep(self.interval)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self.cloud:
            self.cloud.disconnect()
