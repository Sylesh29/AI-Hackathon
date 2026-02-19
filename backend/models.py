from __future__ import annotations

from pydantic import BaseModel, Field


class IncidentSummary(BaseModel):
    id: str
    name: str
    description: str


class SimulateRequest(BaseModel):
    incident_id: str = Field(..., min_length=1)


class AgentLog(BaseModel):
    agent: str
    message: str


class PipelineResult(BaseModel):
    incident_id: str
    incident_name: str
    logs: list[AgentLog]
    reasoning: str
    patch: str
    metrics_before: dict
    metrics_after: dict
    memory_used: bool
    memory_written: bool


class MemoryEntry(BaseModel):
    signature: str
    fix: str
    outcome: str
