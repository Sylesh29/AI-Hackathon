from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.config import Settings
from app.memory.json_repository import JsonMemoryRepository
from app.memory.store import build_repository


class MemoryStoreFallbackTests(unittest.TestCase):
    def test_dev_falls_back_to_json_when_sqlite_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                ENV="development",
                ALLOWED_ORIGINS=["http://localhost:5173"],
                MEMORY_BACKEND="sqlite",
                MEMORY_DB_URL="not-a-valid-db-url",
                MEMORY_STORE_PATH=Path(tmp) / "memory.json",
            )
            repo = build_repository(settings)
            self.assertIsInstance(repo, JsonMemoryRepository)

    def test_non_dev_raises_when_sqlite_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                ENV="production",
                ALLOWED_ORIGINS=["https://example.com"],
                API_KEY="test-key",
                MEMORY_BACKEND="sqlite",
                MEMORY_DB_URL="not-a-valid-db-url",
                MEMORY_STORE_PATH=Path(tmp) / "memory.json",
            )
            with self.assertRaises(Exception):
                build_repository(settings)


if __name__ == "__main__":
    unittest.main()
