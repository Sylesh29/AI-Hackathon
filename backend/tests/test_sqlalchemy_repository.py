from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.memory.sqlalchemy_repository import SqlAlchemyMemoryRepository


class SqlAlchemyMemoryRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "memory.db"
        self.repo = SqlAlchemyMemoryRepository(f"sqlite:///{self.db_path}")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_add_find_and_top_entries(self) -> None:
        created = self.repo.add_or_update("sig-a", "fix-a", "success")
        self.assertTrue(created)

        found = self.repo.find_fix("sig-a")
        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found.signature, "sig-a")
        self.assertEqual(found.fix, "fix-a")
        self.assertEqual(found.outcome, "success")
        self.assertGreaterEqual(found.uses, 2)

        self.repo.add_or_update("sig-b", "fix-b", "success")
        top = self.repo.top_entries(limit=5)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0].signature, "sig-a")

    def test_readiness_check(self) -> None:
        ok, detail = self.repo.readiness_check()
        self.assertTrue(ok)
        self.assertIn("accessible", detail)


if __name__ == "__main__":
    unittest.main()
