from __future__ import annotations

from typing import Any

from ..llm.client import generate_with_resilience


def diagnose(
    root_cause: str,
    memory_fix: str | None,
    signature: str,
    request_id: str = "unknown",
) -> dict[str, Any]:
    if memory_fix:
        return {
            "agent": "diagnose",
            "message": f"Memory hit on '{signature}'. Reusing fix.",
            "reasoning": f"Reused prior successful fix for signature '{signature}'.",
            "fix": memory_fix,
            "model_metrics": {
                "model": "memory-hit",
                "latency_ms": 0.0,
                "attempts": 0,
                "fallback_used": False,
            },
        }

    fallback_reasoning = f"Derived fix from root cause: {root_cause}."
    prompt = (
        "Provide concise root cause reasoning for incident automation. "
        f"Signature: {signature}. Root cause: {root_cause}."
    )
    llm = generate_with_resilience(
        purpose="diagnose_reasoning",
        prompt=prompt,
        fallback_text=fallback_reasoning,
        request_id=request_id,
    )
    return {
        "agent": "diagnose",
        "message": f"Root cause identified: {root_cause}",
        "reasoning": llm.text,
        "fix": None,
        "model_metrics": {
            "model": llm.model,
            "latency_ms": llm.latency_ms,
            "attempts": llm.attempts,
            "fallback_used": llm.fallback_used,
        },
    }
