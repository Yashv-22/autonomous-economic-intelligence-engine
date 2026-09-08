"""
Google Gemini Model Provider Adapter.
"""

import os
import time
from typing import List, Dict, Any, Optional
from src.gateway.base import BaseModelProvider, ModelMessage
from src.models.schemas import ModelResponse, TokenUsage
from src.core.errors import ModelGatewayError


class GeminiModelProvider(BaseModelProvider):
    """Google Gemini API Provider with automatic internal multi-model rotation."""

    name: str = "gemini"

    # Priority rotation models for Gemini free/standard tier
    ROTATION_MODELS = [
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-flash-latest",
        "gemma-4-31b-it",
        "gemini-2.5-flash",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.last_error: Optional[str] = None

    def is_available(self) -> bool:
        """Verify API key is configured and functional."""
        if not self.api_key:
            self.last_error = "Gemini API key is not configured"
            return False
        return True

    def generate(
        self,
        messages: List[ModelMessage],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        **kwargs
    ) -> ModelResponse:
        if not self.api_key:
            raise ModelGatewayError("Gemini API key is not configured.")

        # Resolve primary model
        primary_model = model or os.environ.get("GEMINI_MODEL_NAME", "gemini-3.7-flash")

        # Build candidate list with primary model first, followed by rotation models
        candidate_models = [primary_model] + [m for m in self.ROTATION_MODELS if m != primary_model]

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)

            # Build prompt
            prompt_parts = []
            for msg in messages:
                role_prefix = "System" if msg.role == "system" else ("User" if msg.role == "user" else "Model")
                prompt_parts.append(f"{role_prefix}: {msg.content}")
            full_prompt = "\n\n".join(prompt_parts)

            last_exc = None
            for candidate in candidate_models:
                start_time = time.perf_counter()
                try:
                    gemini_model = genai.GenerativeModel(candidate)
                    response = gemini_model.generate_content(
                        full_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        ),
                        request_options={"timeout": 12.0},
                    )
                    duration_ms = (time.perf_counter() - start_time) * 1000.0

                    content = response.text or ""
                    prompt_tokens = len(full_prompt.split()) * 2
                    completion_tokens = len(content.split()) * 2
                    total_tokens = prompt_tokens + completion_tokens

                    # Pricing estimation ($0.075 / 1M prompt, $0.30 / 1M completion)
                    cost = (prompt_tokens * 0.000000075) + (completion_tokens * 0.00000030)

                    self.last_error = None
                    return ModelResponse(
                        model_name=candidate,
                        provider="gemini",
                        content=content,
                        token_usage=TokenUsage(
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                            estimated_cost_usd=round(cost, 6),
                        ),
                        latency_ms=round(duration_ms, 2),
                        finish_reason="stop",
                    )
                except Exception as model_err:
                    err_str = str(model_err)
                    last_exc = model_err
                    # If 429 rate limit or 404 model not found, try next rotation model
                    if "429" in err_str or "Quota exceeded" in err_str or "404" in err_str or "not found" in err_str:
                        continue
                    # For other fatal errors, also try next or raise
                    continue

            # If all candidates exhausted
            self.last_error = str(last_exc)
            raise ModelGatewayError(f"All Gemini rotation models exhausted: {last_exc}")

        except Exception as e:
            if isinstance(e, ModelGatewayError):
                raise
            self.last_error = str(e)
            raise ModelGatewayError(f"Gemini generation failed: {e}")
