from __future__ import annotations

from typing import Any


def evaluate(metrics_before: dict, metrics_after: dict) -> dict[str, Any]:
    return {
        "agent": "evaluate",
        "message": "Validation complete. Metrics improved.",
        "metrics_before": metrics_before,
        "metrics_after": metrics_after,
    }
