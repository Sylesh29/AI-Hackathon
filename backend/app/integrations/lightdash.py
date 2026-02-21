from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from ..config import Settings


def detect_incident_type(metrics: dict[str, Any]) -> str | None:
    p95 = metrics.get("p95_latency_ms")
    err = metrics.get("error_rate")
    rss = metrics.get("rss_gb")
    gc_pause = metrics.get("gc_pause_ms")
    rate_429 = metrics.get("rate_429")
    qps = metrics.get("api_qps")

    if isinstance(p95, (int, float)) and isinstance(err, (int, float)):
        if p95 > 1100 and err > 2:
            return "db_timeout"
    if isinstance(rss, (int, float)) and isinstance(gc_pause, (int, float)):
        if rss > 2.4 and gc_pause > 400:
            return "memory_leak"
    if isinstance(rate_429, (int, float)) and isinstance(qps, (int, float)):
        if rate_429 > 15 and qps > 1200:
            return "rate_limit"
    return None


class LightdashClient:
    def __init__(self, settings: Settings) -> None:
        self._api_url = settings.LIGHTDASH_API_URL
        self._api_key = settings.LIGHTDASH_API_KEY
        self._project = settings.LIGHTDASH_PROJECT or "autopilotops"

    @property
    def configured(self) -> bool:
        return bool(self._api_url)

    def fetch_metrics(self) -> dict[str, Any]:
        if not self._api_url:
            return self._simulated_metrics()

        req = urllib.request.Request(
            self._api_url,
            headers={
                "Accept": "application/json",
                **({"Authorization": self._authorization_header()} if self._api_key else {}),
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
                    return payload["data"]
                if isinstance(payload, dict):
                    return payload
                return {"raw": payload}
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
            return self._simulated_metrics()

    def _simulated_metrics(self) -> dict[str, Any]:
        slot = int(time.time() // 20) % 3
        if slot == 0:
            return {
                "source": "lightdash-simulated",
                "project": self._project,
                "p95_latency_ms": 1320,
                "error_rate": 2.8,
            }
        if slot == 1:
            return {
                "source": "lightdash-simulated",
                "project": self._project,
                "rss_gb": 2.9,
                "gc_pause_ms": 610,
            }
        return {
            "source": "lightdash-simulated",
            "project": self._project,
            "rate_429": 22,
            "api_qps": 1550,
        }

    def _authorization_header(self) -> str:
        if not self._api_key:
            return ""
        if self._api_key.startswith("ApiKey "):
            return self._api_key
        return f"ApiKey {self._api_key}"
