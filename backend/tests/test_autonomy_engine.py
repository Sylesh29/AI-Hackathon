from __future__ import annotations

import unittest

from app.autonomy.engine import AutonomyEngine
from app.integrations.lightdash import detect_incident_type
from app.models import PipelineResult


class _FakeLightdash:
    configured = True

    def __init__(self, metrics: dict[str, object]) -> None:
        self._metrics = metrics

    def fetch_metrics(self) -> dict[str, object]:
        return self._metrics


class _FakeAiria:
    configured = True

    def publish_action(self, payload):  # type: ignore[no-untyped-def]
        return {"provider": "airia", "status": "sent", "echo_incident": payload.get("incident_type")}


class _FakeModulate:
    configured = True

    def send_voice_summary(self, summary_text: str) -> dict[str, str]:
        return {"provider": "modulate", "status": "sent", "summary": summary_text[:32]}


def _pipeline(memory_used: bool) -> PipelineResult:
    return PipelineResult(
        incident_type="db_timeout",
        signature="sig",
        logs=[],
        reasoning="reason",
        patch="patch",
        sandbox_result="sandbox_passed",
        metrics_before={"p95_latency_ms": 1200},
        metrics_after={"p95_latency_ms": 200},
        model_metrics=None,
        memory_used=memory_used,
        memory_persisted=True,
    )


class AutonomyEngineTests(unittest.TestCase):
    def test_detect_incident_type(self) -> None:
        self.assertEqual(detect_incident_type({"p95_latency_ms": 1300, "error_rate": 3.0}), "db_timeout")
        self.assertEqual(detect_incident_type({"rss_gb": 2.7, "gc_pause_ms": 500}), "memory_leak")
        self.assertEqual(detect_incident_type({"rate_429": 20, "api_qps": 1300}), "rate_limit")
        self.assertIsNone(detect_incident_type({"p95_latency_ms": 300, "error_rate": 0.2}))

    def test_run_once_records_learning(self) -> None:
        engine = AutonomyEngine(
            enabled=False,
            poll_seconds=20,
            max_runs=10,
            run_pipeline=lambda incident_type, request_id: _pipeline(memory_used=True),  # type: ignore[return-value]
            lightdash=_FakeLightdash({"p95_latency_ms": 1300, "error_rate": 2.6}),
            airia=_FakeAiria(),
            modulate=_FakeModulate(),
        )
        result = engine.run_once()
        self.assertTrue(result["triggered"])
        status = engine.status()
        self.assertEqual(status["total_runs"], 1)
        self.assertEqual(status["memory_hit_rate_percent"], 100.0)
        runs = engine.recent_runs(limit=5)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["incident_type"], "db_timeout")


if __name__ == "__main__":
    unittest.main()
