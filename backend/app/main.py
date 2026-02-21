from __future__ import annotations

import logging
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .agents.diagnose import diagnose
from .agents.evaluate import evaluate
from .agents.monitor import monitor
from .agents.patch import patch as patch_agent
from .agents.sandbox import sandbox as sandbox_agent
from .autonomy import AutonomyEngine
from .config import get_settings
from .integrations import AiriaClient, LightdashClient, ModulateClient
from .logging_utils import configure_logging
from .middleware import error_response, register_security_middleware
from .memory.store import add_or_update, find_fix, readiness_check, top_entries
from .models import (
    AutonomyRunOnceEnvelope,
    AutonomyRunOnceResponse,
    AutonomyRunsEnvelope,
    AutonomyRunsResponse,
    AutonomyStatusEnvelope,
    AutonomyStatusResponse,
    ErrorResponse,
    HealthEnvelope,
    HealthResponse,
    MemoryEnvelope,
    MemoryResponse,
    PipelineResultEnvelope,
    PipelineResult,
    RunPipelineRequest,
    ReadyEnvelope,
    ReadyResponse,
    SimulateIncidentEnvelope,
    SimulateIncidentRequest,
    SimulateIncidentResponse,
    StatusEnvelope,
    StatusResponse,
)
from .simulator.incidents import INCIDENTS
from .simulator.simulate import simulate_incident


settings = get_settings()
configure_logging(settings.effective_log_level, settings.ENV)
logger = logging.getLogger(__name__)
logger.info(
    "startup",
    extra={
        "event": "startup",
    },
)


app = FastAPI(
    title=f"AutoPilotOps ({settings.ENV})",
    version="0.2.0",
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_security_middleware(app, settings)

_START_TIME = time.monotonic()
_lightdash = LightdashClient(settings)
_airia = AiriaClient(settings)
_modulate = ModulateClient(settings)
_autonomy = AutonomyEngine(
    enabled=settings.AUTONOMY_ENABLED,
    poll_seconds=settings.AUTONOMY_POLL_SECONDS,
    max_runs=settings.AUTONOMY_MAX_RUNS,
    run_pipeline=lambda incident_type, request_id: _execute_pipeline(incident_type, request_id),  # noqa: E731
    lightdash=_lightdash,
    airia=_airia,
    modulate=_modulate,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    details = None
    if isinstance(exc.detail, str):
        message = exc.detail
    elif isinstance(exc.detail, dict):
        message = str(exc.detail.get("message") or "Request failed.")
        details = exc.detail
    else:
        message = "Request failed."
        details = exc.detail
    return error_response(
        request,
        status_code=exc.status_code,
        code=f"http_{exc.status_code}",
        message=message,
        details=details,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        request,
        status_code=422,
        code="validation_error",
        message="Request validation failed.",
        details=exc.errors(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(
        "unhandled_exception",
        extra={
            "event": "unhandled_exception",
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
    )
    return error_response(
        request,
        status_code=500,
        code="internal_server_error",
        message="Internal server error.",
    )


@app.get(
    "/status",
    response_model=StatusEnvelope,
    responses={
        500: {"model": ErrorResponse},
    },
)
def status(request: Request) -> StatusEnvelope:
    return StatusEnvelope(
        request_id=request.state.request_id,
        data=StatusResponse(status="ok", uptime_seconds=time.monotonic() - _START_TIME),
    )


@app.get(
    "/health",
    response_model=HealthEnvelope,
    responses={
        500: {"model": ErrorResponse},
    },
)
def health(request: Request) -> HealthEnvelope:
    return HealthEnvelope(
        request_id=request.state.request_id,
        data=HealthResponse(status="ok"),
    )


@app.get(
    "/ready",
    response_model=ReadyEnvelope,
    responses={
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def ready(request: Request) -> ReadyEnvelope:
    memory_ok, memory_detail = readiness_check()
    checks = {"memory_store": memory_detail}
    if not memory_ok:
        raise HTTPException(status_code=503, detail={"message": "Service not ready.", "checks": checks})
    return ReadyEnvelope(
        request_id=request.state.request_id,
        data=ReadyResponse(status="ready", checks=checks),
    )


@app.on_event("startup")
def on_startup() -> None:
    _autonomy.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    _autonomy.stop()


def _execute_pipeline(incident_type: str, request_id: str) -> PipelineResult:
    if incident_type not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Unknown incident_type")

    timings_ms: dict[str, float] = {}
    pipeline_started = time.perf_counter()

    def _measure(name: str, fn):
        started = time.perf_counter()
        value = fn()
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        timings_ms[name] = elapsed_ms
        logger.info(
            "pipeline_step_completed",
            extra={
                "event": "pipeline_step_completed",
                "request_id": request_id,
                "incident_type": incident_type,
                "timings_ms": {name: elapsed_ms},
            },
        )
        return value

    incident = INCIDENTS[incident_type]
    logs = []

    logs.append(_measure("monitor", lambda: monitor(incident_type, incident["symptoms"])))

    memory_entry = _measure("memory_lookup", lambda: find_fix(incident["signature"]))
    memory_fix = memory_entry["fix"] if memory_entry else None
    diagnosis = _measure(
        "diagnose",
        lambda: diagnose(
            incident["root_cause"],
            memory_fix,
            incident["signature"],
            request_id=request_id,
        ),
    )
    logs.append({"agent": diagnosis["agent"], "message": diagnosis["message"]})

    fix = memory_fix or incident["fix"]
    if memory_fix is None:
        diagnosis_reasoning = diagnosis["reasoning"]
    else:
        diagnosis_reasoning = diagnosis["reasoning"]

    patch_plan = _measure("patch_plan", lambda: incident["patch"])
    logs.append(_measure("patch", lambda: patch_agent(patch_plan)))

    sandbox_result = _measure("sandbox", lambda: sandbox_agent(patch_plan))
    logs.append({"agent": sandbox_result["agent"], "message": sandbox_result["message"]})

    evaluation = _measure(
        "evaluate",
        lambda: evaluate(incident["metrics_before"], incident["metrics_after"]),
    )
    logs.append({"agent": evaluation["agent"], "message": evaluation["message"]})

    memory_persisted = _measure(
        "memory_persist",
        lambda: add_or_update(incident["signature"], fix, "success"),
    )

    timings_ms["total"] = round((time.perf_counter() - pipeline_started) * 1000, 2)
    logger.info(
        "pipeline_completed",
        extra={
            "event": "pipeline_completed",
            "request_id": request_id,
            "incident_type": incident_type,
            "timings_ms": timings_ms,
        },
    )

    return PipelineResult(
        incident_type=incident_type,
        signature=incident["signature"],
        logs=logs,
        reasoning=diagnosis_reasoning,
        patch=patch_plan,
        sandbox_result=sandbox_result["result"],
        metrics_before=incident["metrics_before"],
        metrics_after=incident["metrics_after"],
        model_metrics=diagnosis.get("model_metrics"),
        memory_used=memory_fix is not None,
        memory_persisted=memory_persisted,
    )


@app.post(
    "/simulate_incident",
    response_model=SimulateIncidentEnvelope,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def simulate(request: Request, body: SimulateIncidentRequest) -> SimulateIncidentEnvelope:
    incident_type = body.incident_type
    if incident_type not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Unknown incident_type")
    payload = simulate_incident(incident_type)
    return SimulateIncidentEnvelope(
        request_id=request.state.request_id,
        data=SimulateIncidentResponse(**payload),
    )


@app.post(
    "/run_pipeline",
    response_model=PipelineResultEnvelope,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def run_pipeline(request: Request, body: RunPipelineRequest) -> PipelineResultEnvelope:
    result = _execute_pipeline(body.incident_type, request.state.request_id)
    return PipelineResultEnvelope(request_id=request.state.request_id, data=result)


@app.get(
    "/memory",
    response_model=MemoryEnvelope,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def get_memory(request: Request) -> MemoryEnvelope:
    return MemoryEnvelope(
        request_id=request.state.request_id,
        data=MemoryResponse(entries=top_entries()),
    )


@app.get(
    "/autonomy/status",
    response_model=AutonomyStatusEnvelope,
    responses={500: {"model": ErrorResponse}},
)
def autonomy_status(request: Request) -> AutonomyStatusEnvelope:
    status = _autonomy.status()
    return AutonomyStatusEnvelope(
        request_id=request.state.request_id,
        data=AutonomyStatusResponse(**status),
    )


@app.get(
    "/autonomy/runs",
    response_model=AutonomyRunsEnvelope,
    responses={500: {"model": ErrorResponse}},
)
def autonomy_runs(request: Request, limit: int = 10) -> AutonomyRunsEnvelope:
    runs = _autonomy.recent_runs(limit=limit)
    return AutonomyRunsEnvelope(
        request_id=request.state.request_id,
        data=AutonomyRunsResponse(runs=runs),
    )


@app.post(
    "/autonomy/run_once",
    response_model=AutonomyRunOnceEnvelope,
    responses={
        401: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def autonomy_run_once(request: Request) -> AutonomyRunOnceEnvelope:
    result = _autonomy.run_once()
    incident_type = result.get("record", {}).get("incident_type") if result.get("record") else None
    return AutonomyRunOnceEnvelope(
        request_id=request.state.request_id,
        data=AutonomyRunOnceResponse(
            triggered=bool(result.get("triggered")),
            reason=result.get("reason"),
            incident_type=incident_type,
            metrics=result.get("metrics", {}),
            record=result.get("record"),
        ),
    )
