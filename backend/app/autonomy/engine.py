from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable

from ..integrations import AiriaClient, LightdashClient, ModulateClient, detect_incident_type
from ..models import PipelineResult

logger = logging.getLogger(__name__)


class AutonomyEngine:
    def __init__(
        self,
        *,
        enabled: bool,
        poll_seconds: int,
        max_runs: int,
        run_pipeline: Callable[[str, str], PipelineResult],
        lightdash: LightdashClient,
        airia: AiriaClient,
        modulate: ModulateClient,
    ) -> None:
        self._enabled = enabled
        self._poll_seconds = max(5, poll_seconds)
        self._run_pipeline = run_pipeline
        self._lightdash = lightdash
        self._airia = airia
        self._modulate = modulate
        self._runs: deque[dict[str, Any]] = deque(maxlen=max(10, max_runs))
        self._last_metrics: dict[str, Any] | None = None
        self._memory_hits = 0
        self._total_runs = 0
        self._last_incident_at: dict[str, float] = {}
        self._cooldown_seconds = 30
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if not self._enabled:
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="autonomy-engine", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def run_once(self) -> dict[str, Any]:
        metrics = self._lightdash.fetch_metrics()
        incident_type = detect_incident_type(metrics)
        with self._lock:
            self._last_metrics = metrics

        if not incident_type:
            return {
                "triggered": False,
                "reason": "No anomaly over thresholds.",
                "metrics": metrics,
            }

        now = time.monotonic()
        with self._lock:
            last_ts = self._last_incident_at.get(incident_type)
            if last_ts and (now - last_ts) < self._cooldown_seconds:
                return {
                    "triggered": False,
                    "reason": f"Cooldown active for {incident_type}.",
                    "metrics": metrics,
                    "incident_type": incident_type,
                }
            self._last_incident_at[incident_type] = now

        request_id = f"auto-{uuid.uuid4()}"
        pipeline = self._run_pipeline(incident_type, request_id)
        impact_score = self._compute_impact_score(pipeline.metrics_before, pipeline.metrics_after)
        summary = (
            f"Autonomous run for {incident_type}: sandbox={pipeline.sandbox_result}, "
            f"memory_used={pipeline.memory_used}, impact_score={impact_score}"
        )
        airia_result = self._airia.publish_action(
            {
                "request_id": request_id,
                "incident_type": incident_type,
                "impact_score": impact_score,
                "memory_used": pipeline.memory_used,
                "reasoning": pipeline.reasoning,
                "patch": pipeline.patch,
            }
        )
        modulate_result = self._modulate.send_voice_summary(summary)
        record = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "request_id": request_id,
            "incident_type": incident_type,
            "impact_score": impact_score,
            "memory_used": pipeline.memory_used,
            "sandbox_result": pipeline.sandbox_result,
            "sponsors": {
                "lightdash": "live" if self._lightdash.configured else "simulated",
                "airia": airia_result,
                "modulate": modulate_result,
            },
        }
        with self._lock:
            self._total_runs += 1
            if pipeline.memory_used:
                self._memory_hits += 1
            self._runs.appendleft(record)

        return {"triggered": True, "record": record, "metrics": metrics}

    def status(self) -> dict[str, Any]:
        with self._lock:
            total = self._total_runs
            memory_hits = self._memory_hits
            memory_hit_rate = round((memory_hits / total) * 100, 2) if total > 0 else 0.0
            learning_score = round(min(100.0, 55.0 + (memory_hit_rate * 0.4)), 2)
            return {
                "enabled": self._enabled,
                "running": bool(self._thread and self._thread.is_alive()),
                "poll_seconds": self._poll_seconds,
                "total_runs": total,
                "memory_hit_rate_percent": memory_hit_rate,
                "learning_score": learning_score,
                "last_metrics": self._last_metrics,
                "sponsor_integrations": {
                    "lightdash": "configured" if self._lightdash.configured else "simulated",
                    "airia": "configured" if self._airia.configured else "simulated",
                    "modulate": "configured" if self._modulate.configured else "simulated",
                },
            }

    def recent_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._runs)[: max(1, min(limit, len(self._runs) or 1))]

    def _loop(self) -> None:
        while not self._stop_event.wait(self._poll_seconds):
            try:
                result = self.run_once()
                logger.info(
                    "autonomy_tick",
                    extra={
                        "event": "autonomy_tick",
                        "incident_type": result.get("record", {}).get("incident_type")
                        if result.get("triggered")
                        else "none",
                    },
                )
            except Exception:
                logger.exception("autonomy_tick_failed", extra={"event": "autonomy_tick_failed"})

    @staticmethod
    def _compute_impact_score(before: dict[str, Any], after: dict[str, Any]) -> int | None:
        deltas: list[float] = []
        for key, before_value in before.items():
            after_value = after.get(key)
            if not isinstance(before_value, (int, float)):
                continue
            if not isinstance(after_value, (int, float)):
                continue
            if before_value <= 0:
                continue
            improvement = (before_value - after_value) / before_value
            deltas.append(max(-1.0, min(1.0, improvement)))
        if not deltas:
            return None
        avg = sum(deltas) / len(deltas)
        return int(round(((avg + 1) / 2) * 100))
