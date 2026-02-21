from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ..config import Settings


class ModulateClient:
    def __init__(self, settings: Settings) -> None:
        self._api_url = settings.MODULATE_API_URL
        self._api_key = settings.MODULATE_API_KEY
        self._voice = settings.MODULATE_VOICE

    @property
    def configured(self) -> bool:
        return bool(self._api_url)

    def send_voice_summary(self, summary_text: str) -> dict[str, Any]:
        if not self._api_url:
            return {"provider": "modulate", "status": "simulated", "detail": "MODULATE_API_URL not configured"}

        body = json.dumps({"text": summary_text, "voice": self._voice}).encode("utf-8")
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
                    "provider": "modulate",
                    "status": "sent",
                    "http_status": response.status,
                }
        except (urllib.error.URLError, TimeoutError) as exc:
            return {
                "provider": "modulate",
                "status": "failed",
                "detail": exc.__class__.__name__,
            }
