from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    _EXTRA_KEYS = {
        "request_id",
        "event",
        "path",
        "method",
        "status_code",
        "duration_ms",
        "incident_type",
        "timings_ms",
    }

    def __init__(self, env: str) -> None:
        super().__init__()
        self.env = env

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "env": self.env,
        }
        for key in self._EXTRA_KEYS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level_name: str, env: str) -> None:
    root = logging.getLogger()
    level = getattr(logging, level_name.upper(), logging.INFO)
    root.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(JsonFormatter(env=env))

    root.handlers.clear()
    root.addHandler(handler)
