from __future__ import annotations

from typing import Any

from .incidents import INCIDENTS


def simulate_incident(incident_type: str) -> dict[str, Any]:
    incident = INCIDENTS[incident_type]
    return {
        "incident_type": incident_type,
        "signature": incident["signature"],
        "symptoms": incident["symptoms"],
        "metrics": incident["metrics_before"],
    }
