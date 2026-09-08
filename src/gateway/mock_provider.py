"""
Deterministic Mock Model Provider for Offline Testing and CI Evaluation.
"""

import time
from typing import List, Dict, Any
from src.gateway.base import BaseModelProvider, ModelMessage
from src.models.schemas import ModelResponse, TokenUsage


class MockModelProvider(BaseModelProvider):
    """Deterministic mock provider simulating LLM generation."""

    name: str = "mock"

    def __init__(self, responses_map: Dict[str, str] = None):
        self.responses_map = responses_map or {}

    def generate(
        self,
        messages: List[ModelMessage],
        model: str = "mock-model",
        temperature: float = 0.0,
        max_tokens: int = 2048,
        **kwargs
    ) -> ModelResponse:
        start_time = time.perf_counter()

        # Concatenate prompt for inspection
        full_prompt = " ".join([m.content for m in messages]).lower()

        # Match specific intent
        if "synthesis" in full_prompt or "executive summary" in full_prompt:
            content = (
                "Executive Synthesis: Enterprise AI operating model transformation requires transitioning "
                "from task-level point assistance to straight-through automated routing (alpha). "
                "Near-universal task adoption currently yields negligible bottom-line earnings impact "
                "because organizations fail to redesign cross-functional handoffs, causing severe downstream velocity drift."
            )
        elif "gap" in full_prompt or "missing variable" in full_prompt:
            content = (
                "Identified Research Gap: Lack of empirical longitudinal data regarding human supervisory review fatigue "
                "under high-throughput agent escalation queues."
            )
        elif "query" in full_prompt or "search" in full_prompt:
            content = "straight-through routing rate human override latency"
        else:
            content = "Analytical reasoning completed with full evidentiary provenance."

        # Check explicit overrides
        for key, custom_text in self.responses_map.items():
            if key.lower() in full_prompt:
                content = custom_text
                break

        duration_ms = (time.perf_counter() - start_time) * 1000.0 + 5.0  # simulate realistic latency
        prompt_tokens = sum(len(m.content.split()) for m in messages) * 2
        completion_tokens = len(content.split()) * 2
        total_tokens = prompt_tokens + completion_tokens

        # Estimated cost ($0.0001 per 1k tokens)
        est_cost = (total_tokens / 1000.0) * 0.0001

        return ModelResponse(
            model_name=model,
            provider="mock",
            content=content,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=round(est_cost, 6),
            ),
            latency_ms=round(duration_ms, 2),
            finish_reason="stop",
        )
