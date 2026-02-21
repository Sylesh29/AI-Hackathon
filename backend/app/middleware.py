from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import Settings

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
logger = logging.getLogger(__name__)


def _ensure_request_id(request: Request) -> str:
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    return request_id


def error_payload(
    request_id: str,
    code: str,
    message: str,
    details: object | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "request_id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details is not None:
        payload["error"]["details"] = details
    return payload


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: object | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or _ensure_request_id(request)
    response = JSONResponse(
        status_code=status_code,
        content=error_payload(request_id=request_id, code=code, message=message, details=details),
    )
    response.headers["X-Request-ID"] = request_id
    return response


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def register_security_middleware(app: FastAPI, settings: Settings) -> None:
    rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)
    rate_limit_lock = Lock()

    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        request_id = _ensure_request_id(request)
        started = time.perf_counter()

        def _log_completed(status_code: int) -> None:
            logger.info(
                "request_completed",
                extra={
                    "event": "request_completed",
                    "request_id": request_id,
                    "method": method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )

        def _fail(
            *,
            status_code: int,
            code: str,
            message: str,
            details: object | None = None,
        ) -> JSONResponse:
            response = error_response(
                request,
                status_code=status_code,
                code=code,
                message=message,
                details=details,
            )
            _log_completed(status_code)
            return response

        method = request.method.upper()
        if method not in _MUTATING_METHODS:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            _log_completed(response.status_code)
            return response

        if settings.API_KEY:
            provided_api_key = request.headers.get("x-api-key")
            if not provided_api_key:
                return _fail(
                    status_code=401,
                    code="auth_missing_api_key",
                    message="Missing API key. Provide X-API-Key header for mutating endpoints.",
                )
            if provided_api_key != settings.API_KEY:
                return _fail(
                    status_code=401,
                    code="auth_invalid_api_key",
                    message="Invalid API key for mutating endpoint.",
                )

        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                return _fail(
                    status_code=400,
                    code="request_invalid_content_length",
                    message="Invalid Content-Length header.",
                )
            if size > settings.MAX_REQUEST_SIZE_BYTES:
                return _fail(
                    status_code=413,
                    code="request_too_large",
                    message=(
                        "Request body too large. "
                        f"Maximum is {settings.MAX_REQUEST_SIZE_BYTES} bytes."
                    ),
                )

        client_ip = _get_client_ip(request)
        now = time.monotonic()
        window_start = now - settings.RATE_LIMIT_WINDOW_SECONDS

        with rate_limit_lock:
            bucket = rate_limit_buckets[client_ip]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= settings.RATE_LIMIT_REQUESTS_PER_WINDOW:
                return _fail(
                    status_code=429,
                    code="rate_limit_exceeded",
                    message=(
                        "Rate limit exceeded for mutating endpoints. "
                        f"Allowed: {settings.RATE_LIMIT_REQUESTS_PER_WINDOW} requests per "
                        f"{settings.RATE_LIMIT_WINDOW_SECONDS} seconds."
                    ),
                )
            bucket.append(now)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        _log_completed(response.status_code)
        return response
