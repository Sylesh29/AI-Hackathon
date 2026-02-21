from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.config import Settings


class ProductionConfigValidationTests(unittest.TestCase):
    def test_production_requires_api_key(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(
                ENV="production",
                ALLOWED_ORIGINS=["https://example.com"],
                API_KEY=None,
            )

    def test_production_requires_https_non_localhost_origins(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(
                ENV="production",
                ALLOWED_ORIGINS=["http://localhost:5173"],
                API_KEY="secret",
            )

    def test_docs_disabled_in_production(self) -> None:
        settings = Settings(
            ENV="production",
            ALLOWED_ORIGINS=["https://example.com"],
            API_KEY="secret",
        )
        self.assertFalse(settings.docs_enabled)


if __name__ == "__main__":
    unittest.main()
