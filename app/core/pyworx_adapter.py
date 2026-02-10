import threading, json, os, time
from pyworxcloud import WorxCloud
from pyworxcloud.events import LandroidEvent
from pyworxcloud.exceptions import AuthorizationError


class PyWorxAdapterError(Exception):
    pass


class PyWorxAdapter:
    def __init__(self, sid, username, password, brand):
        self.sid = sid
        self.username = username
        self.password = password
        self.brand = brand
        self.running = False
        self.error = None
        self._cloud = None
        self._original_on_update = None
        self._events_registered = False
        self._data_path = f"/app/data/{sid}"

    def prepare(self):
        if self._cloud:
            return

        cloud = WorxCloud(self.username, self.password, self.brand)
        self._cloud = cloud

        self._original_on_update = cloud._on_update

        def on_update(payload):
            try:
                parsed = json.loads(payload)
            except Exception:
                parsed = payload
            self._dump("mqtt.json", {"ts": time.time(), "payload": parsed})
            return self._original_on_update(payload)

        cloud._on_update = on_update

        try:
            auth = cloud.authenticate()
        except AuthorizationError as exc:
            raise PyWorxAdapterError(f"Authentication failed: {exc}") from exc
        if not auth:
            raise PyWorxAdapterError("Authentication failed: invalid credentials")

        try:
            connected = cloud.connect()
        except Exception as exc:
            raise PyWorxAdapterError(f"Connection failed: {exc}") from exc
        if not connected:
            raise PyWorxAdapterError("No devices found for account")

        os.makedirs(self._data_path, exist_ok=True)
        for _, device in cloud.devices.items():
            self._dump_http(device)

        cloud._events.set_handler(LandroidEvent.DATA_RECEIVED, self._on_data_received)
        self._events_registered = True

    def start(self):
        if not self._cloud:
            self.prepare()

        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            while self.running:
                time.sleep(1)
        finally:
            self._cleanup()

    def _dump(self, name, payload):
        os.makedirs(self._data_path, exist_ok=True)
        with open(f"{self._data_path}/{name}", "a") as f:
            f.write(json.dumps(payload, default=str,indent=2) + "\n")

    def stop(self):
        self.running = False
        self._cleanup()

    def _dump_http(self, device):
        payload = None
        if hasattr(device, "json_data") and device.json_data:
            payload = device.json_data
        elif hasattr(device, "raw_data") and device.raw_data:
            payload = device.raw_data
        elif (
            hasattr(device, "last_status")
            and device.last_status
            and "payload" in device.last_status
        ):
            payload = device.last_status["payload"]
        if payload is not None:
            self._dump("http.json", {"ts": time.time(), "payload": payload})

    def _on_data_received(self, name, device):
        self._dump_http(device)

    def _cleanup(self):
        if not self._cloud:
            return

        if self._events_registered:
            try:
                self._cloud._events.del_handler(LandroidEvent.DATA_RECEIVED)
            except Exception:
                pass
            self._events_registered = False

        if self._original_on_update:
            try:
                self._cloud._on_update = self._original_on_update
            except Exception:
                pass
            self._original_on_update = None

        try:
            self._cloud.disconnect()
        except Exception:
            pass
        self._cloud = None
