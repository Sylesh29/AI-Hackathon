from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class MemoryRecord:
    signature: str
    fix: str
    outcome: str
    uses: int = 0
    last_used: str | None = None


class MemoryRepository(Protocol):
    def readiness_check(self) -> tuple[bool, str]: ...

    def find_fix(self, signature: str) -> MemoryRecord | None: ...

    def add_or_update(self, signature: str, fix: str, outcome: str) -> bool: ...

    def top_entries(self, limit: int = 5) -> list[MemoryRecord]: ...
