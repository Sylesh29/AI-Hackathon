from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ..config import Settings


class AiriaClient:
    def __init__(self, settings: Settings) -> None:
        self._api_url = settings.AIRIA_API_URL
        self._api_key = settings.AIRIA_API_KEY

    @property
    def configured(self) -> bool:
        return bool(self._api_url)

    def publish_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._api_url:
            return {"provider": "airia", "status": "simulated", "detail": "AIRIA_API_URL not configured"}

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._api_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                return {
                    "provider": "airia",
                    "status": "sent",
                    "http_status": response.status,
                }
        except (urllib.error.URLError, TimeoutError) as exc:
            return {
                "provider": "airia",
                "status": "failed",
                "detail": exc.__class__.__name__,
            }
