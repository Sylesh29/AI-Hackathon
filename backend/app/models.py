from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


IncidentType = Literal["db_timeout", "memory_leak", "rate_limit"]


class SimulateIncidentRequest(BaseModel):
    incident_type: IncidentType


class SimulateIncidentResponse(BaseModel):
    incident_type: IncidentType
    signature: str
    symptoms: list[str]
    metrics: dict[str, Any]


class RunPipelineRequest(BaseModel):
    incident_type: IncidentType


class AgentLog(BaseModel):
    agent: str
    message: str


class PipelineResult(BaseModel):
    incident_type: IncidentType
    signature: str
    logs: list[AgentLog]
    reasoning: str
    patch: str
    sandbox_result: str
    metrics_before: dict[str, Any]
    metrics_after: dict[str, Any]
    model_metrics: dict[str, Any] | None = None
    memory_used: bool
    memory_persisted: bool


class MemoryEntry(BaseModel):
    signature: str
    fix: str
    outcome: str
    uses: int = 0
    last_used: str | None = None


class MemoryResponse(BaseModel):
    entries: list[MemoryEntry]


class StatusResponse(BaseModel):
    status: str
    uptime_seconds: float


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    checks: dict[str, str]


class ErrorInfo(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    request_id: str
    error: ErrorInfo


class StatusEnvelope(BaseModel):
    request_id: str
    data: StatusResponse


class SimulateIncidentEnvelope(BaseModel):
    request_id: str
    data: SimulateIncidentResponse


class PipelineResultEnvelope(BaseModel):
    request_id: str
    data: PipelineResult


class MemoryEnvelope(BaseModel):
    request_id: str
    data: MemoryResponse


class HealthEnvelope(BaseModel):
    request_id: str
    data: HealthResponse


class ReadyEnvelope(BaseModel):
    request_id: str
    data: ReadyResponse


class AutonomyStatusResponse(BaseModel):
    enabled: bool
    running: bool
    poll_seconds: int
    total_runs: int
    memory_hit_rate_percent: float
    learning_score: float
    last_metrics: dict[str, Any] | None = None
    sponsor_integrations: dict[str, str]


class AutonomyRunsResponse(BaseModel):
    runs: list[dict[str, Any]]


class AutonomyRunOnceResponse(BaseModel):
    triggered: bool
    reason: str | None = None
    incident_type: str | None = None
    metrics: dict[str, Any]
    record: dict[str, Any] | None = None


class AutonomyStatusEnvelope(BaseModel):
    request_id: str
    data: AutonomyStatusResponse


class AutonomyRunsEnvelope(BaseModel):
    request_id: str
    data: AutonomyRunsResponse


class AutonomyRunOnceEnvelope(BaseModel):
    request_id: str
    data: AutonomyRunOnceResponse
