from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .agents import run_pipeline
from .incidents import INCIDENTS
from .memory import load_memory, save_memory
from .models import IncidentSummary, PipelineResult, SimulateRequest


app = FastAPI(title="AutoPilotOps", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/incidents", response_model=list[IncidentSummary])
def list_incidents() -> list[IncidentSummary]:
    return [
        IncidentSummary(
            id=incident_id,
            name=data["name"],
            description=data["description"],
        )
        for incident_id, data in INCIDENTS.items()
    ]


@app.post("/simulate", response_model=PipelineResult)
def simulate(request: SimulateRequest) -> PipelineResult:
    incident_id = request.incident_id
    if incident_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Unknown incident_id")
    result = run_pipeline(incident_id)
    return PipelineResult(**result)


@app.get("/memory")
def get_memory() -> dict:
    return {"entries": load_memory()}


@app.post("/memory/clear")
def clear_memory() -> dict:
    save_memory([])
    return {"cleared": True}
