from __future__ import annotations

from typing import Any


def sandbox(patch_plan: str) -> dict[str, Any]:
    return {
        "agent": "sandbox",
        "message": f"Applied patch in sandbox: {patch_plan}",
        "result": "sandbox_passed",
    }
