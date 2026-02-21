from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .repository import MemoryRecord


class JsonMemoryRepository:
    def __init__(self, memory_path: Path) -> None:
        self.memory_path = memory_path

    def _ensure_memory_file(self) -> None:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.memory_path.exists():
            self.memory_path.write_text("[]", encoding="utf-8")

    def _load_entries(self) -> list[dict[str, Any]]:
        self._ensure_memory_file()
        return json.loads(self.memory_path.read_text(encoding="utf-8"))

    def _save_entries(self, entries: list[dict[str, Any]]) -> None:
        self._ensure_memory_file()
        self.memory_path.write_text(json.dumps(entries, indent=2, sort_keys=True), encoding="utf-8")

    def readiness_check(self) -> tuple[bool, str]:
        try:
            self._ensure_memory_file()
            self._load_entries()
            return True, "memory_store_accessible_json"
        except Exception as exc:  # pragma: no cover - defensive
            return False, f"memory_store_unavailable_json: {exc.__class__.__name__}"

    def find_fix(self, signature: str) -> MemoryRecord | None:
        entries = self._load_entries()
        for entry in entries:
            if entry.get("signature") == signature and entry.get("outcome") == "success":
                entry["uses"] = int(entry.get("uses", 0)) + 1
                entry["last_used"] = datetime.now(tz=timezone.utc).isoformat()
                self._save_entries(entries)
                return MemoryRecord(**entry)
        return None

    def add_or_update(self, signature: str, fix: str, outcome: str) -> bool:
        entries = self._load_entries()
        for entry in entries:
            if entry.get("signature") == signature and entry.get("fix") == fix:
                entry["outcome"] = outcome
                entry["uses"] = int(entry.get("uses", 0)) + 1
                entry["last_used"] = datetime.now(tz=timezone.utc).isoformat()
                self._save_entries(entries)
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
        self._save_entries(entries)
        return True

    def top_entries(self, limit: int = 5) -> list[MemoryRecord]:
        entries = self._load_entries()
        entries.sort(key=lambda item: (item.get("uses", 0), item.get("last_used") or ""), reverse=True)
        return [MemoryRecord(**item) for item in entries[:limit]]
