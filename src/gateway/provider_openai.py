"""
OpenAI Model Provider Adapter.
Supports direct REST API calls over HTTPS and native openai SDK if present.
"""

import os
import json
import time
import urllib.request
from typing import List, Dict, Any, Optional
from src.gateway.base import BaseModelProvider, ModelMessage
from src.models.schemas import ModelResponse, TokenUsage
from src.core.errors import ModelGatewayError
from src.core.logging import logger


class OpenAIModelProvider(BaseModelProvider):
    """OpenAI API Provider (GPT-4o, GPT-4o-mini, GPT-4-turbo, o1, o3-mini)."""

    name: str = "openai"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.last_error: Optional[str] = None

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured and valid."""
        if not self.api_key:
            self.last_error = "OpenAI API key not configured (OPENAI_API_KEY)"
            return False
        try:
            url = f"{self.base_url}/models"
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "Autonomous-AI-Operating-Model/1.0",
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                self.last_error = None
                return resp.status == 200
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.last_error = "Invalid or expired API Key (401 Unauthorized)"
            else:
                self.last_error = f"HTTP {e.code} Error"
            return False
        except Exception as e:
            self.last_error = f"Unreachable: {e}"
            return False

    def generate(
        self,
        messages: List[ModelMessage],
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: int = 2048,
        **kwargs
    ) -> ModelResponse:
        if not self.api_key:
            raise ModelGatewayError("OpenAI API key is not configured (OPENAI_API_KEY).")

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start_time = time.perf_counter()

        # Try native SDK if installed, otherwise robust HTTPS REST request
        try:
            try:
                import openai
                client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": m.role, "content": m.content} for m in messages],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                content = resp.choices[0].message.content or ""
                prompt_tokens = resp.usage.prompt_tokens if resp.usage else len(json.dumps(payload)) // 4
                completion_tokens = resp.usage.completion_tokens if resp.usage else len(content) // 4
                total_tokens = prompt_tokens + completion_tokens
            except ImportError:
                # Direct REST fallback over standard urllib (zero extra dependency)
                url = f"{self.base_url}/chat/completions"
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                        "User-Agent": "Autonomous-AI-Operating-Model/1.0",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=45) as response:
                    raw = json.loads(response.read().decode("utf-8"))

                duration_ms = (time.perf_counter() - start_time) * 1000.0
                content = raw["choices"][0]["message"]["content"] or ""
                usage = raw.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", len(json.dumps(payload)) // 4)
                completion_tokens = usage.get("completion_tokens", len(content) // 4)
                total_tokens = prompt_tokens + completion_tokens

            # Cost estimation ($2.50 / 1M prompt, $10.00 / 1M completion for GPT-4o)
            cost = (prompt_tokens * 0.0000025) + (completion_tokens * 0.0000100)

            return ModelResponse(
                model_name=model,
                provider="openai",
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
        except Exception as e:
            raise ModelGatewayError(f"OpenAI generation failed: {e}")
