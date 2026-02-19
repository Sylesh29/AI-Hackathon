from __future__ import annotations

from typing import Any


def patch(patch_plan: str) -> dict[str, Any]:
    return {
        "agent": "patch",
        "message": f"Generated patch plan: {patch_plan}",
    }
