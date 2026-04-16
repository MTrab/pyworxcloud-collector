import threading, json, os, time, asyncio, inspect, logging
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
        self._task = None
        self._logger = logging.getLogger(__name__)
        self._file_locks = {}

    async def prepare(self):
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
            # write MQTT entries to the session folder (same as http.json)
            self._dump("mqtt.json", {"ts": time.time(), "payload": parsed})
            return self._original_on_update(payload)

        cloud._on_update = on_update

        try:
            auth = await cloud.authenticate()
        except AuthorizationError as exc:
            raise PyWorxAdapterError(f"Authentication failed: {exc}") from exc
        if not auth:
            raise PyWorxAdapterError("Authentication failed: invalid credentials")

        try:
            connected = await cloud.connect()
        except Exception as exc:
            raise PyWorxAdapterError(f"Connection failed: {exc}") from exc
        if not connected:
            raise PyWorxAdapterError("No devices found for account")

        os.makedirs(self._data_path, exist_ok=True)
        # collect device metadata (serial, name, model) for API use
        self.devices_info = []
        # log discovered devices for diagnostics
        logger = logging.getLogger(__name__)
        logger.debug("Discovered cloud.devices keys=%s", list(cloud.devices.keys()))
        for key, device in cloud.devices.items():
            # canonical serial if available
            serial = None
            for attr in ("serial_number", "serialNumber", "serial", "device_id", "id"):
                val = getattr(device, attr, None)
                if val:
                    serial = str(val)
                    break
            if not serial:
                serial = str(key)

            # try to get name/model from device attributes or last_status payload
            name = getattr(device, "name", None) or getattr(device, "device_name", None)
            model = getattr(device, "model", None) or getattr(device, "device_model", None)
            try:
                if (not name or not model) and hasattr(device, "last_status") and device.last_status:
                    payload = device.last_status.get("payload") if isinstance(device.last_status, dict) else None
                    if isinstance(payload, dict):
                        name = name or payload.get("name") or payload.get("deviceName")
                        model = model or payload.get("model") or payload.get("deviceModel")
            except Exception:
                pass

            self.devices_info.append({"key": str(key), "serial": serial, "name": name, "model": model})

            # initial HTTP dump under canonical
            self._dump_http(device)

        logger.info("Collector devices_info=%s", self.devices_info)

        cloud._events.set_handler(LandroidEvent.DATA_RECEIVED, self._on_data_received)
        self._events_registered = True

    async def start(self):
        if not self._cloud:
            await self.prepare()

        self.running = True
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run())

    async def _run(self):
        try:
            while self.running:
                await asyncio.sleep(1)
        finally:
            await self._cleanup()

    def _dump(self, name, payload, subdir=None):
        try:
            base = self._data_path if not subdir else os.path.join(self._data_path, str(subdir))
            os.makedirs(base, exist_ok=True)
            path = f"{base}/{name}"
            try:
                size = len(json.dumps(payload, default=str)) if payload is not None else 0
            except Exception:
                size = 0
            self._logger.info("Writing %s (%d bytes) to %s", name, size, path)
            # ensure per-file locking to avoid races and accidental overwrites
            lock = self._file_locks.get(path)
            if lock is None:
                lock = threading.Lock()
                self._file_locks[path] = lock
            with lock:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(payload, default=str, indent=2) + "\n")
                    try:
                        f.flush()
                        os.fsync(f.fileno())
                    except Exception:
                        pass
        except Exception as exc:
            self._logger.exception("Failed to write %s: %s", name, exc)

    async def stop(self):
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
        await self._cleanup()

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

        # build device metadata for the http.json entry
        def _meta_from_device(dev):
            serial = None
            for attr in ("serial_number", "serialNumber", "serial", "device_id", "id"):
                try:
                    val = getattr(dev, attr, None)
                except Exception:
                    val = None
                if val:
                    serial = str(val)
                    break
            if not serial:
                try:
                    serial = str(next(iter(getattr(dev, "__dict__", {}).values())))
                except Exception:
                    serial = None

            name = getattr(dev, "name", None) or getattr(dev, "device_name", None)
            model = getattr(dev, "model", None) or getattr(dev, "device_model", None)
            try:
                if (not name or not model) and hasattr(dev, "last_status") and dev.last_status:
                    payload_inner = dev.last_status.get("payload") if isinstance(dev.last_status, dict) else None
                    if isinstance(payload_inner, dict):
                        name = name or payload_inner.get("name") or payload_inner.get("deviceName")
                        model = model or payload_inner.get("model") or payload_inner.get("deviceModel")
            except Exception:
                pass

            return {"serial": serial, "name": name, "model": model, "key": str(getattr(dev, "id", getattr(dev, "device_id", "")))}

        meta = _meta_from_device(device)

        if payload is not None:
            self._logger.info("_dump_http: found payload for device (serial=%s), writing http.json", meta.get("serial"))
            self._dump("http.json", {"ts": time.time(), "device": meta, "payload": payload})
        else:
            self._logger.debug("_dump_http: no payload available for device %s", getattr(device, "id", getattr(device, "device_id", "unknown")))

    def _on_data_received(self, name, device):
        self._logger.debug("_on_data_received: name=%s device=%s", name, getattr(device, "id", None))
        self._dump_http(device)

    async def _cleanup(self):
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
            await self._cloud.disconnect()
        except Exception:
            pass
        self._cloud = None
