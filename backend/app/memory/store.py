from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MEMORY_PATH = Path(__file__).resolve().parent.parent / "data" / "memory.json"


def _ensure_memory_file() -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_PATH.exists():
        MEMORY_PATH.write_text("[]", encoding="utf-8")


def _load_entries() -> list[dict[str, Any]]:
    _ensure_memory_file()
    return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))


def _save_entries(entries: list[dict[str, Any]]) -> None:
    _ensure_memory_file()
    MEMORY_PATH.write_text(json.dumps(entries, indent=2, sort_keys=True), encoding="utf-8")


def find_fix(signature: str) -> dict[str, Any] | None:
    entries = _load_entries()
    for entry in entries:
        if entry.get("signature") == signature and entry.get("outcome") == "success":
            entry["uses"] = int(entry.get("uses", 0)) + 1
            entry["last_used"] = datetime.now(tz=timezone.utc).isoformat()
            _save_entries(entries)
            return entry
    return None


def add_or_update(signature: str, fix: str, outcome: str) -> bool:
    entries = _load_entries()
    for entry in entries:
        if entry.get("signature") == signature and entry.get("fix") == fix:
            entry["outcome"] = outcome
            entry["uses"] = int(entry.get("uses", 0)) + 1
            entry["last_used"] = datetime.now(tz=timezone.utc).isoformat()
            _save_entries(entries)
            return False
    entries.append(
        {
            "signature": signature,
            "fix": fix,
            "outcome": outcome,
            "uses": 1,
            "last_used": datetime.now(tz=timezone.utc).isoformat(),
        }
    )
    _save_entries(entries)
    return True


def top_entries(limit: int = 5) -> list[dict[str, Any]]:
    entries = _load_entries()
    entries.sort(key=lambda item: (item.get("uses", 0), item.get("last_used") or ""), reverse=True)
    return entries[:limit]
