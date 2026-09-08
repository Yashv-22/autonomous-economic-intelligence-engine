"""
FreeLLMAPI Model Provider Adapter.
Integrates FreeLLMAPI (http://localhost:3001/v1) as an OpenAI-compatible free-tier inference backend.
"""

import os
import json
import time
import sqlite3
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

from src.gateway.base import BaseModelProvider, ModelMessage
from src.models.schemas import ModelResponse, TokenUsage
from src.core.errors import ModelGatewayError
from src.core.logging import logger


class FreeLLMAPIModelProvider(BaseModelProvider):
    """
    Provider adapter connecting to the FreeLLMAPI routing layer.
    Exposes unified multi-provider fallback and quota-managed free models.
    """

    name: str = "freellmapi"

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        db_path: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ):
        raw_base = (
            base_url
            or os.environ.get("FREELLMAPI_BASE_URL")
            or os.environ.get("FREELLMAPI_URL")
            or "http://localhost:3001/v1"
        ).rstrip("/")
        if not raw_base.endswith("/v1"):
            raw_base = f"{raw_base}/v1"
        self.base_url = raw_base
        self.default_model = default_model or os.environ.get("FREELLMAPI_DEFAULT_MODEL", "auto")
        self.timeout_seconds = timeout_seconds
        self.db_path = db_path or os.environ.get(
            "FREEAPI_DB_PATH",
            os.path.join("infrastructure", "FreeLLMAPI", "server", "data", "freeapi.db"),
        )
        self.api_key = api_key or os.environ.get("FREELLMAPI_API_KEY") or self._discover_unified_key()
        self.last_error: Optional[str] = None

    def _discover_unified_key(self) -> Optional[str]:
        """Auto-discover unified API key from local FreeLLMAPI database if present."""
        if not os.path.exists(self.db_path):
            return None
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'unified_api_key'")
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                return row[0].strip()
        except Exception as e:
            logger.debug(f"FreeLLMAPI unified key auto-discovery skipped: {e}")
        return None

    def is_available(self) -> bool:
        """Check if FreeLLMAPI endpoint is reachable and authenticated."""
        if not self.api_key:
            self.last_error = "FreeLLMAPI API key not configured"
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
        except Exception as e:
            self.last_error = f"Unreachable: {e}"
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """Retrieve available model catalog from FreeLLMAPI."""
        if not self.api_key:
            raise ModelGatewayError("FreeLLMAPI API key is not configured.")

        url = f"{self.base_url}/models"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Autonomous-AI-Operating-Model/1.0",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload.get("data", [])
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise ModelGatewayError(f"FreeLLMAPI models listing failed (HTTP {e.code}): {err_body}")
        except Exception as e:
            raise ModelGatewayError(f"FreeLLMAPI models listing unreachable: {e}")

    def generate(
        self,
        messages: List[ModelMessage],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        **kwargs,
    ) -> ModelResponse:
        """Send chat completion prompt to FreeLLMAPI and return standardized ModelResponse."""
        if not self.api_key:
            raise ModelGatewayError(
                "FreeLLMAPI API key is not configured (FREELLMAPI_API_KEY or server/data/freeapi.db)."
            )

        chosen_model = model or self.default_model
        payload = {
            "model": chosen_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

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

        start_time = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="replace")
            raise ModelGatewayError(f"FreeLLMAPI request failed (HTTP {e.code}): {err_msg}")
        except urllib.error.URLError as e:
            raise ModelGatewayError(f"FreeLLMAPI connection failed: {e.reason}")
        except Exception as e:
            raise ModelGatewayError(f"FreeLLMAPI generation error: {e}")

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        choices = raw.get("choices", [])
        if not choices:
            raise ModelGatewayError(f"FreeLLMAPI returned response without choices: {raw}")

        choice = choices[0]
        content = choice.get("message", {}).get("content") or ""
        finish_reason = choice.get("finish_reason", "stop")
        actual_model = raw.get("model") or chosen_model

        usage = raw.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", len(json.dumps(payload)) // 4)
        completion_tokens = usage.get("completion_tokens", len(content) // 4)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        # Free tier provider pool cost is $0.00
        return ModelResponse(
            model_name=actual_model,
            provider="freellmapi",
            content=content,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=0.0,
            ),
            latency_ms=round(duration_ms, 2),
            finish_reason=finish_reason,
        )
