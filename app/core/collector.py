
import json
from pathlib import Path
from datetime import datetime

class CollectorSink:
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.http = []
        self.mqtt = []

    def record_http(self, payload: dict):
        self.http.append(payload)

    def record_mqtt(self, payload: dict):
        self.mqtt.append(payload)

    def dump(self):
        self.session_dir.mkdir(parents=True, exist_ok=True)
        (self.session_dir / "http.json").write_text(json.dumps(self.http, indent=2))
        (self.session_dir / "mqtt.json").write_text(json.dumps(self.mqtt, indent=2))

    def summary(self):
        return {
            "http": len(self.http),
            "mqtt": len(self.mqtt),
        }
