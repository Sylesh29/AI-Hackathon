from __future__ import annotations

import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .agents.diagnose import diagnose
from .agents.evaluate import evaluate
from .agents.monitor import monitor
from .agents.patch import patch as patch_agent
from .agents.sandbox import sandbox as sandbox_agent
from .memory.store import add_or_update, find_fix, top_entries
from .models import (
    MemoryResponse,
    PipelineResult,
    RunPipelineRequest,
    SimulateIncidentRequest,
    SimulateIncidentResponse,
    StatusResponse,
)
from .simulator.incidents import INCIDENTS
from .simulator.simulate import simulate_incident


app = FastAPI(title="AutoPilotOps", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_START_TIME = time.monotonic()


@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    return StatusResponse(status="ok", uptime_seconds=time.monotonic() - _START_TIME)


@app.post("/simulate_incident", response_model=SimulateIncidentResponse)
def simulate(request: SimulateIncidentRequest) -> SimulateIncidentResponse:
    incident_type = request.incident_type
    if incident_type not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Unknown incident_type")
    payload = simulate_incident(incident_type)
    return SimulateIncidentResponse(**payload)


@app.post("/run_pipeline", response_model=PipelineResult)
def run_pipeline(request: RunPipelineRequest) -> PipelineResult:
    incident_type = request.incident_type
    if incident_type not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Unknown incident_type")

    incident = INCIDENTS[incident_type]
    logs = []

    logs.append(monitor(incident_type, incident["symptoms"]))

    memory_entry = find_fix(incident["signature"])
    memory_fix = memory_entry["fix"] if memory_entry else None
    diagnosis = diagnose(incident["root_cause"], memory_fix, incident["signature"])
    logs.append({"agent": diagnosis["agent"], "message": diagnosis["message"]})

    fix = memory_fix or incident["fix"]
    if memory_fix is None:
        diagnosis_reasoning = diagnosis["reasoning"]
    else:
        diagnosis_reasoning = diagnosis["reasoning"]

    patch_plan = incident["patch"]
    logs.append(patch_agent(patch_plan))

    sandbox_result = sandbox_agent(patch_plan)
    logs.append({"agent": sandbox_result["agent"], "message": sandbox_result["message"]})

    evaluation = evaluate(incident["metrics_before"], incident["metrics_after"])
    logs.append({"agent": evaluation["agent"], "message": evaluation["message"]})

    memory_persisted = add_or_update(incident["signature"], fix, "success")

    return PipelineResult(
        incident_type=incident_type,
        signature=incident["signature"],
        logs=logs,
        reasoning=diagnosis_reasoning,
        patch=patch_plan,
        sandbox_result=sandbox_result["result"],
        metrics_before=incident["metrics_before"],
        metrics_after=incident["metrics_after"],
        memory_used=memory_fix is not None,
        memory_persisted=memory_persisted,
    )


@app.get("/memory", response_model=MemoryResponse)
def get_memory() -> MemoryResponse:
    return MemoryResponse(entries=top_entries())
