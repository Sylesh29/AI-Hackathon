from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_DEFAULT_MEMORY_PATH = Path(__file__).resolve().parent / "data" / "memory.json"
_DEFAULT_MEMORY_DB_PATH = Path(__file__).resolve().parent / "data" / "memory.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: str = "development"
    LOG_LEVEL: str | None = None
    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    API_KEY: str | None = None
    LLM_MODEL: str = "deterministic-sim-v1"
    LLM_TIMEOUT_SECONDS: float = 2.0
    LLM_MAX_RETRIES: int = 2
    LLM_RETRY_BACKOFF_MS: int = 150
    MEMORY_BACKEND: str = "sqlite"
    MEMORY_DB_URL: str = f"sqlite:///{_DEFAULT_MEMORY_DB_PATH}"
    MEMORY_STORE_PATH: Path = _DEFAULT_MEMORY_PATH
    MAX_REQUEST_SIZE_BYTES: int = 1_048_576
    RATE_LIMIT_REQUESTS_PER_WINDOW: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    AUTONOMY_ENABLED: bool = True
    AUTONOMY_POLL_SECONDS: int = 20
    AUTONOMY_MAX_RUNS: int = 50
    LIGHTDASH_API_URL: https://app.lightdash.cloud/api/v1 | None = None
    LIGHTDASH_API_KEY: ldpat_4bc12dddf454a54e9dc0aff285d135e5 | None = None
    LIGHTDASH_PROJECT: f337a7fb-c600-4212-945c-87ec9eba8a32 | None = None
    LIGHTDASH_INSTANCE_URL: str = "https://app.lightdash.cloud"
    LIGHTDASH_PROJECT_UUID: str | None = None
    AIRIA_API_URL: str | None = None
    AIRIA_API_KEY: ak-MTU3NDYzMTAwNXwxNzcxNzA0ODQzMzIzfHRpLVUxVk9XUzFQY0dWdUlGSmxaMmx6ZEhKaGRHbHZiaTFCYVhKcFlTQkdjbVZsfDF8MTcwMjY2NDQ1MiAg | None = None
    MODULATE_API_URL: str | None = None
    MODULATE_API_KEY: 4c5b488d-b3ac-c831-07b7-432d730dcf95 | None = None
    MODULATE_VOICE: str | None = None

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            origins = [item.strip() for item in value.split(",") if item.strip()]
            return origins
        return value

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_allowed_origins(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("ALLOWED_ORIGINS must contain at least one origin.")
        if "*" in value:
            raise ValueError("ALLOWED_ORIGINS cannot include '*'. Use explicit origins.")
        return value

    @model_validator(mode="after")
    def validate_environment_rules(self) -> "Settings":
        if self.is_production:
            if not self.API_KEY:
                raise ValueError("API_KEY is required when ENV=production.")
            for origin in self.ALLOWED_ORIGINS:
                normalized = origin.lower()
                if "localhost" in normalized or "127.0.0.1" in normalized:
                    raise ValueError(
                        "ALLOWED_ORIGINS must not include localhost/127.0.0.1 in production."
                    )
                if not normalized.startswith("https://"):
                    raise ValueError("ALLOWED_ORIGINS must use https:// in production.")
        return self

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @property
    def docs_enabled(self) -> bool:
        return not self.is_production

    @property
    def effective_log_level(self) -> str:
        if self.LOG_LEVEL:
            return self.LOG_LEVEL
        if self.is_production:
            return "INFO"
        return "DEBUG"


@lru_cache
def get_settings() -> Settings:
    return Settings()
