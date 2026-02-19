from __future__ import annotations

from typing import Any


def monitor(incident_type: str, symptoms: list[str]) -> dict[str, Any]:
    return {
        "agent": "monitor",
        "message": f"Incident '{incident_type}' detected: " + ", ".join(symptoms),
    }
