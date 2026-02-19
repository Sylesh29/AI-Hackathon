from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MEMORY_PATH = Path(__file__).parent / "data" / "memory.json"


def _ensure_memory_file() -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_PATH.exists():
        MEMORY_PATH.write_text("[]", encoding="utf-8")


def load_memory() -> list[dict[str, Any]]:
    _ensure_memory_file()
    return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))


def save_memory(entries: list[dict[str, Any]]) -> None:
    _ensure_memory_file()
    MEMORY_PATH.write_text(json.dumps(entries, indent=2, sort_keys=True), encoding="utf-8")


def find_fix(signature: str) -> str | None:
    entries = load_memory()
    for entry in entries:
        if entry.get("signature") == signature and entry.get("outcome") == "success":
            return entry.get("fix")
    return None


def add_pattern(signature: str, fix: str, outcome: str) -> bool:
    entries = load_memory()
    already = any(
        entry.get("signature") == signature and entry.get("fix") == fix for entry in entries
    )
    if already:
        return False
    entries.append({"signature": signature, "fix": fix, "outcome": outcome})
    save_memory(entries)
    return True
