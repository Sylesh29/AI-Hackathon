from __future__ import annotations

from typing import Any


def diagnose(root_cause: str, memory_fix: str | None, signature: str) -> dict[str, Any]:
    if memory_fix:
        return {
            "agent": "diagnose",
            "message": f"Memory hit on '{signature}'. Reusing fix.",
            "reasoning": f"Reused prior successful fix for signature '{signature}'.",
            "fix": memory_fix,
        }
    return {
        "agent": "diagnose",
        "message": f"Root cause identified: {root_cause}",
        "reasoning": f"Derived fix from root cause: {root_cause}.",
        "fix": None,
    }
