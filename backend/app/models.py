from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


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
