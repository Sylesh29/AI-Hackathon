from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from typing import Callable

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class LLMCallError(RuntimeError):
    pass


@dataclass
class LLMResult:
    text: str
    model: str
    latency_ms: float
    attempts: int
    fallback_used: bool


def _default_provider(prompt: str, model: str) -> str:
    # Deterministic local provider for demo/dev unless a real provider is added.
    return f"[{model}] {prompt[:240]}"


def _call_with_timeout(fn: Callable[[], str], timeout_seconds: float) -> str:
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise TimeoutError("LLM call timed out") from exc


def generate_with_resilience(
    *,
    purpose: str,
    prompt: str,
    fallback_text: str,
    request_id: str,
    provider: Callable[[str, str], str] | None = None,
    settings: Settings | None = None,
) -> LLMResult:
    cfg = settings or get_settings()
    fn = provider or _default_provider
    timeout_seconds = max(0.1, float(cfg.LLM_TIMEOUT_SECONDS))
    retries = max(0, int(cfg.LLM_MAX_RETRIES))
    backoff_ms = max(0, int(cfg.LLM_RETRY_BACKOFF_MS))
    model = cfg.LLM_MODEL

    started = time.perf_counter()
    attempts = 0
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        attempts = attempt + 1
        attempt_started = time.perf_counter()
        try:
            text = _call_with_timeout(lambda: fn(prompt, model), timeout_seconds)
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                "llm_call_completed",
                extra={
                    "event": "llm_call_completed",
                    "request_id": request_id,
                    "purpose": purpose,
                    "model": model,
                    "attempt": attempts,
                    "status": "ok",
                    "duration_ms": round((time.perf_counter() - attempt_started) * 1000, 2),
                    "latency_ms": latency_ms,
                    "prompt_chars": len(prompt),
                    "fallback_used": False,
                },
            )
            return LLMResult(
                text=text,
                model=model,
                latency_ms=latency_ms,
                attempts=attempts,
                fallback_used=False,
            )
        except Exception as exc:
            last_error = exc
            logger.warning(
                "llm_call_attempt_failed",
                extra={
                    "event": "llm_call_attempt_failed",
                    "request_id": request_id,
                    "purpose": purpose,
                    "model": model,
                    "attempt": attempts,
                    "duration_ms": round((time.perf_counter() - attempt_started) * 1000, 2),
                    "error_type": exc.__class__.__name__,
                    "prompt_chars": len(prompt),
                },
            )
            if attempt < retries and backoff_ms > 0:
                time.sleep(backoff_ms / 1000.0)

    total_latency_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.warning(
        "llm_call_fallback",
        extra={
            "event": "llm_call_fallback",
            "request_id": request_id,
            "purpose": purpose,
            "model": model,
            "attempts": attempts,
            "latency_ms": total_latency_ms,
            "error_type": last_error.__class__.__name__ if last_error else "unknown",
            "fallback_used": True,
        },
    )
    return LLMResult(
        text=fallback_text,
        model=model,
        latency_ms=total_latency_ms,
        attempts=attempts,
        fallback_used=True,
    )
