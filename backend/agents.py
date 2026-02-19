from __future__ import annotations

from typing import Any

from .incidents import INCIDENTS
from .memory import add_pattern, find_fix


def run_pipeline(incident_id: str) -> dict[str, Any]:
    incident = INCIDENTS[incident_id]

    logs: list[dict[str, str]] = []

    logs.append(
        {
            "agent": "monitor",
            "message": f"Detected incident '{incident['name']}' with symptoms: "
            + ", ".join(incident["symptoms"]),
        }
    )

    signature = incident["signature"]
    memory_fix = find_fix(signature)
    memory_used = memory_fix is not None

    if memory_used:
        logs.append(
            {
                "agent": "diagnose",
                "message": f"Matched memory signature '{signature}'.",
            }
        )
        fix = memory_fix
        reasoning = f"Reused prior successful fix for signature '{signature}'."
    else:
        logs.append(
            {
                "agent": "diagnose",
                "message": f"Root cause: {incident['root_cause']}",
            }
        )
        fix = incident["fix"]
        reasoning = (
            f"Derived fix from symptoms and root cause: {incident['root_cause']}."
        )

    logs.append(
        {
            "agent": "patch",
            "message": f"Applying patch: {incident['patch']}",
        }
    )

    logs.append(
        {
            "agent": "evaluate",
            "message": "Metrics improved and SLOs back to normal.",
        }
    )

    memory_written = add_pattern(signature, fix, "success")

    return {
        "incident_id": incident_id,
        "incident_name": incident["name"],
        "logs": logs,
        "reasoning": reasoning,
        "patch": incident["patch"],
        "metrics_before": incident["metrics_before"],
        "metrics_after": incident["metrics_after"],
        "memory_used": memory_used,
        "memory_written": memory_written,
    }
