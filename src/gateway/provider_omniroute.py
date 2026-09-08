"""
OmniRoute Model Provider Adapter.
Integrates OmniRoute (http://127.0.0.1:20128/v1) as an OpenAI-compatible model gateway
with dynamic workload aliasing, circuit-breaking, and token auditing.
Enforces zero database coupling: credentials are strictly passed via environment variables.
"""

import os
import json
import time
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

from src.gateway.base import BaseModelProvider, ModelMessage
from src.models.schemas import ModelResponse, TokenUsage
from src.core.errors import ModelGatewayError
from src.core.logging import logger


class OmniRouteModelProvider(BaseModelProvider):
    """
    Decoupled provider adapter for the OmniRoute gateway.
    Exposes OpenAI-compatible endpoints with workload aliasing
    ('research-reasoning', 'research-fast', 'research-general').
    """

    name: str = "omniroute"

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ):
        raw_base = (
            base_url
            or os.environ.get("OMNIROUTE_BASE_URL")
            or "http://127.0.0.1:20128/v1"
        ).rstrip("/")
        if not raw_base.endswith("/v1"):
            raw_base = f"{raw_base}/v1"

        self.base_url = raw_base
        self.api_key = api_key or os.environ.get("OMNIROUTE_API_KEY")
        self.default_model = default_model or os.environ.get("OMNIROUTE_DEFAULT_MODEL", "research-general")
        self.timeout_seconds = timeout_seconds
        self.last_error: Optional[str] = None

    def is_available(self) -> bool:
        """Check if OmniRoute endpoint is reachable and authenticated."""
        if not self.api_key:
            self.last_error = "OmniRoute API key not configured"
            return False
        try:
            url = f"{self.base_url}/models"
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "Autonomous-AI-Economic-Engine/1.0",
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                self.last_error = None
                return resp.status == 200
        except Exception as e:
            self.last_error = f"Unreachable: {e}"
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """Retrieve available model catalog from OmniRoute."""
        if not self.api_key:
            raise ModelGatewayError("OmniRoute API key is not configured.")

        url = f"{self.base_url}/models"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Autonomous-AI-Economic-Engine/1.0",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload.get("data", [])
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise ModelGatewayError(f"OmniRoute models listing failed (HTTP {e.code}): {err_body}")
        except Exception as e:
            raise ModelGatewayError(f"OmniRoute models listing unreachable: {e}")

    def generate(
        self,
        messages: List[ModelMessage],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        """
        Execute chat completion through OmniRoute gateway.
        """
        if not self.api_key:
            raise ModelGatewayError(
                "OmniRoute API key is not configured. Set OMNIROUTE_API_KEY in environment or .env."
            )

        chosen_model = model or self.default_model
        payload = {
            "model": chosen_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data_bytes,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Autonomous-AI-Economic-Engine/1.0",
            },
            method="POST",
        )

        start_time = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
                res_json = json.loads(raw_body)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            logger.error(f"OmniRoute API HTTP {e.code} Error: {err_body}")
            raise ModelGatewayError(f"OmniRoute error (HTTP {e.code}): {err_body}")
        except Exception as e:
            logger.error(f"OmniRoute connection failure: {e}")
            raise ModelGatewayError(f"Failed connecting to OmniRoute at {self.base_url}: {e}")

        latency_ms = int((time.time() - start_time) * 1000)

        # Parse OpenAI-format response
        try:
            choices = res_json.get("choices", [])
            if not choices:
                raise ModelGatewayError(f"OmniRoute returned empty choices array: {res_json}")

            text_content = choices[0].get("message", {}).get("content", "")
            usage_dict = res_json.get("usage", {})
            prompt_tokens = usage_dict.get("prompt_tokens", len(json.dumps(payload)) // 4)
            completion_tokens = usage_dict.get("completion_tokens", len(text_content) // 4)
            total_tokens = usage_dict.get("total_tokens", prompt_tokens + completion_tokens)

            estimated_cost = 0.0

            return ModelResponse(
                content=text_content,
                model_name=res_json.get("model", chosen_model),
                provider=self.name,
                latency_ms=latency_ms,
                token_usage=TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=estimated_cost,
                ),
                raw_response=res_json,
            )
        except Exception as e:
            if isinstance(e, ModelGatewayError):
                raise
            raise ModelGatewayError(f"Failed parsing OmniRoute response: {e}")
