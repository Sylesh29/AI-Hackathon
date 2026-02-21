from __future__ import annotations

import logging
from threading import Lock
from typing import Any

from ..config import Settings, get_settings
from .json_repository import JsonMemoryRepository
from .repository import MemoryRepository
from .sqlalchemy_repository import SqlAlchemyMemoryRepository

logger = logging.getLogger(__name__)

_repo_lock = Lock()
_repository: MemoryRepository | None = None


def build_repository(settings: Settings) -> MemoryRepository:
    backend = settings.MEMORY_BACKEND.strip().lower()

    if backend == "json":
        return JsonMemoryRepository(settings.MEMORY_STORE_PATH)

    if backend not in {"sqlite", "auto"}:
        raise ValueError("MEMORY_BACKEND must be one of: sqlite, json, auto")

    try:
        return SqlAlchemyMemoryRepository(settings.MEMORY_DB_URL)
    except Exception as exc:
        if settings.ENV.lower() == "development":
            logger.warning(
                "memory_backend_fallback",
                extra={
                    "event": "memory_backend_fallback",
                    "fallback_reason": "SQLite memory backend unavailable; falling back to JSON store.",
                    "error": exc.__class__.__name__,
                },
            )
            return JsonMemoryRepository(settings.MEMORY_STORE_PATH)
        raise


def get_repository() -> MemoryRepository:
    global _repository
    if _repository is not None:
        return _repository

    with _repo_lock:
        if _repository is None:
            _repository = build_repository(get_settings())
        return _repository


def reset_repository_for_tests() -> None:
    global _repository
    with _repo_lock:
        _repository = None


def readiness_check() -> tuple[bool, str]:
    return get_repository().readiness_check()


def find_fix(signature: str) -> dict[str, Any] | None:
    record = get_repository().find_fix(signature)
    return record.__dict__ if record else None


def add_or_update(signature: str, fix: str, outcome: str) -> bool:
    return get_repository().add_or_update(signature, fix, outcome)


def top_entries(limit: int = 5) -> list[dict[str, Any]]:
    return [entry.__dict__ for entry in get_repository().top_entries(limit)]
