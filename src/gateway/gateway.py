import time
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from src.gateway.base import BaseModelProvider, ModelMessage
from src.gateway.mock_provider import MockModelProvider
from src.gateway.provider_gemini import GeminiModelProvider
from src.gateway.provider_openai import OpenAIModelProvider
from src.gateway.provider_freellmapi import FreeLLMAPIModelProvider
from src.gateway.provider_omniroute import OmniRouteModelProvider
from src.models.schemas import ModelResponse, TokenUsage
from src.core.config import settings
from src.core.logging import logger
from src.core.errors import ModelGatewayError
from src.core.events import event_bus, SystemEvent


class TaskCapability(str, Enum):
    """Capability tier requirements for specialized agentic workloads."""
    FAST = "FAST"
    REASONING = "REASONING"
    ECONOMIC_REASONING = "ECONOMIC_REASONING"


TASK_CAPABILITY_MAP: Dict[str, TaskCapability] = {
    # Fast / High-throughput tasks
    "SOURCE_TRIAGE": TaskCapability.FAST,
    "CLASSIFICATION": TaskCapability.FAST,
    "CLAIM_EXTRACTION": TaskCapability.FAST,
    "UI_SUMMARIZATION": TaskCapability.FAST,
    "ENTITY_EXTRACTION": TaskCapability.FAST,
    "FAST": TaskCapability.FAST,
    # Reasoning tasks
    "QUERY_GENERATION": TaskCapability.REASONING,
    "CONTRADICTION_ANALYSIS": TaskCapability.REASONING,
    "HYPOTHESIS_GENERATION": TaskCapability.REASONING,
    "RESEARCH_SYNTHESIS": TaskCapability.REASONING,
    "VALIDATION": TaskCapability.REASONING,
    "REASONING": TaskCapability.REASONING,
    # Economic intelligence tasks
    "OPPORTUNITY_ANALYSIS": TaskCapability.ECONOMIC_REASONING,
    "BUSINESS_MODEL_ANALYSIS": TaskCapability.ECONOMIC_REASONING,
    "ECONOMIC_VALIDATION": TaskCapability.ECONOMIC_REASONING,
    "SOLUTION_DESIGN": TaskCapability.ECONOMIC_REASONING,
    "ECONOMIC_REASONING": TaskCapability.ECONOMIC_REASONING,
}


class ModelGateway:
    """Central gateway routing LLM requests with capability-aware fallback and cost metering."""

    def __init__(self, default_provider: Optional[str] = None):
        self.default_provider = default_provider or settings.model.default_provider or "omniroute"
        self.providers: Dict[str, BaseModelProvider] = {
            "omniroute": OmniRouteModelProvider(),
            "gemini": GeminiModelProvider(),
            "freellmapi": FreeLLMAPIModelProvider(),
            "openai": OpenAIModelProvider(),
            "mock": MockModelProvider(),
        }
        self.total_tokens_consumed = 0
        self.total_cost_usd = 0.0
        self.last_lifecycle_matrix: Dict[str, Dict[str, Any]] = {}

    def register_provider(self, provider: BaseModelProvider):
        """Register a custom model provider."""
        self.providers[provider.name] = provider

    def resolve_model_for_capability(
        self,
        provider_name: str,
        capability: TaskCapability,
        explicit_model: Optional[str] = None,
    ) -> str:
        """Resolve the optimal model name for a given provider and capability tier."""
        if explicit_model:
            return explicit_model

        if provider_name == "omniroute":
            if capability == TaskCapability.FAST:
                return "auto/best-fast"
            elif capability == TaskCapability.ECONOMIC_REASONING:
                return "auto/best-reasoning"
            return "auto/best-chat"

        elif provider_name == "freellmapi":
            return settings.model.freellmapi_default_model or "auto"

        elif provider_name == "gemini":
            return settings.model.gemini_model_name

        elif provider_name == "openai":
            if capability == TaskCapability.FAST:
                return "gpt-4o-mini"
            return settings.model.openai_model_name

        return "mock-model"

    def generate(
        self,
        messages: List[ModelMessage],
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        task_class: Optional[Union[TaskCapability, str]] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        correlation_id: str = "",
        actor_id: str = "agent",
    ) -> ModelResponse:
        """
        Execute generation with capability-aware model selection and resilient fallback.
        Records exact 8-stage lifecycle telemetry:
        configured -> reachable -> eligible -> selected -> attempted -> succeeded/failed -> fallback -> executed
        """
        # Resolve capability tier
        cap = TaskCapability.REASONING
        if task_class:
            if isinstance(task_class, TaskCapability):
                cap = task_class
            elif isinstance(task_class, str):
                cap = TASK_CAPABILITY_MAP.get(task_class.upper(), TaskCapability.REASONING)

        chosen_provider_name = provider_name or self.default_provider
        provider = self.providers.get(chosen_provider_name)

        # Reset per-call lifecycle tracker
        lifecycle: Dict[str, Dict[str, Any]] = {
            name: {
                "selected": False,
                "attempted": False,
                "succeeded": False,
                "failed": False,
                "fallback": False,
                "executed": False,
                "reason": "Not selected for this task",
                "model": "-",
                "latency_ms": 0.0,
            }
            for name in self.providers.keys()
        }

        # Fallback to mock if provider is unknown
        if not provider:
            logger.warning(f"Provider '{chosen_provider_name}' not available. Falling back to 'mock'.")
            provider = self.providers["mock"]

        lifecycle[provider.name]["selected"] = True
        model_name = self.resolve_model_for_capability(provider.name, cap, explicit_model=model)
        lifecycle[provider.name]["model"] = model_name

        response: Optional[ModelResponse] = None
        attempted_providers = {provider.name}

        # 1. Attempt primary provider
        lifecycle[provider.name]["attempted"] = True
        try:
            response = provider.generate(
                messages=messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if response:
                lifecycle[provider.name]["succeeded"] = True
                lifecycle[provider.name]["executed"] = True
                lifecycle[provider.name]["reason"] = f"Active inference completed ({response.latency_ms:.0f}ms)"
                lifecycle[provider.name]["latency_ms"] = response.latency_ms
        except Exception as e:
            lifecycle[provider.name]["failed"] = True
            lifecycle[provider.name]["succeeded"] = False
            lifecycle[provider.name]["fallback"] = True
            lifecycle[provider.name]["reason"] = f"Primary failed: {e}"
            logger.warning(f"Primary provider '{provider.name}' failed for capability '{cap.value}': {e}.")

        # 2. Capability-aware fallback chain across all configured providers
        if response is None:
            priority_order = ["omniroute", "gemini", "freellmapi", "openai"]
            candidate_chain = [p for p in priority_order if p in self.providers and p not in attempted_providers]

            for fb_name in candidate_chain:
                fb_prov = self.providers.get(fb_name)
                if not fb_prov:
                    continue
                attempted_providers.add(fb_name)
                fb_model = self.resolve_model_for_capability(fb_name, cap)
                lifecycle[fb_name]["selected"] = True
                lifecycle[fb_name]["attempted"] = True
                lifecycle[fb_name]["model"] = fb_model
                try:
                    logger.info(f"Attempting capability-aware fallback to '{fb_name}' (Model: {fb_model})...")
                    response = fb_prov.generate(
                        messages=messages,
                        model=fb_model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    if response:
                        lifecycle[fb_name]["succeeded"] = True
                        lifecycle[fb_name]["executed"] = True
                        lifecycle[fb_name]["reason"] = f"Fallback completed successfully ({response.latency_ms:.0f}ms)"
                        lifecycle[fb_name]["latency_ms"] = response.latency_ms
                        break
                except Exception as fb_err:
                    lifecycle[fb_name]["failed"] = True
                    lifecycle[fb_name]["succeeded"] = False
                    lifecycle[fb_name]["fallback"] = True
                    lifecycle[fb_name]["reason"] = f"Fallback failed: {fb_err}"
                    logger.warning(f"Fallback to '{fb_name}' failed: {fb_err}.")

        # 3. Final safety: Mock provider ensures zero runtime crash
        if response is None:
            logger.info("Falling back to deterministic 'mock' provider.")
            fallback = self.providers["mock"]
            lifecycle["mock"]["selected"] = True
            lifecycle["mock"]["attempted"] = True
            lifecycle["mock"]["model"] = "mock-fallback"
            response = fallback.generate(
                messages=messages,
                model="mock-fallback",
                temperature=temperature,
                max_tokens=max_tokens,
            )
            lifecycle["mock"]["succeeded"] = True
            lifecycle["mock"]["executed"] = True
            lifecycle["mock"]["reason"] = "Safety fallback executed"

        self.last_lifecycle_matrix = lifecycle

        # Accumulate metrics
        self.total_tokens_consumed += response.token_usage.total_tokens
        self.total_cost_usd += response.token_usage.estimated_cost_usd

        # Emit observability event
        event_bus.publish(
            SystemEvent(
                event_type="MODEL_GENERATION_COMPLETED",
                correlation_id=correlation_id,
                agent_id=actor_id,
                payload={
                    "provider": response.provider,
                    "model": response.model_name,
                    "capability": cap.value,
                    "tokens": response.token_usage.total_tokens,
                    "cost_usd": response.token_usage.estimated_cost_usd,
                    "latency_ms": response.latency_ms,
                    "lifecycle": lifecycle.get(response.provider, {}),
                },
            )
        )

        return response

    def get_operational_matrix(self, live_probe: bool = False) -> Dict[str, Any]:
        """
        Return the 8-dimensional operational matrix for all registered providers:
        Configured, Reachable, Eligible, Selected, Attempted, Succeeded, Failed, Fallback, Executed, Reason.
        When live_probe=True, conducts real-time availability checks and measures live ping latency.
        """
        matrix = {}
        for name, p in self.providers.items():
            if name == "mock":
                continue
            is_configured = bool(getattr(p, "api_key", None) or getattr(p, "base_url", None))
            is_reachable = False
            probe_err = None
            ping_ms = 0.0

            try:
                if hasattr(p, "is_available"):
                    t0 = time.perf_counter()
                    is_reachable = p.is_available()
                    ping_ms = round((time.perf_counter() - t0) * 1000.0, 1)
                else:
                    is_reachable = is_configured
            except Exception as e:
                is_reachable = False
                probe_err = str(e)

            last_run = self.last_lifecycle_matrix.get(name, {})

            # Resolve default model representation
            default_mod = (
                getattr(p, "default_model", None)
                or getattr(settings.model, f"{name}_model_name", None)
                or getattr(settings.model, f"{name}_default_model", None)
                or "-"
            )
            active_model = last_run.get("model") if last_run.get("model") and last_run.get("model") != "-" else default_mod

            # Determine clear, truthful operational status
            if is_reachable:
                if last_run.get("executed"):
                    reason = f"Active ({last_run.get('latency_ms', 0):.0f}ms) — {last_run.get('reason', '')}"
                elif ping_ms > 0:
                    reason = f"Online & Ready ({ping_ms:.0f}ms ping)"
                else:
                    reason = "Online & Ready"
            else:
                reason = getattr(p, "last_error", None) or probe_err or "Offline / Daemon Inactive"

            matrix[name] = {
                "name": name,
                "configured": is_configured,
                "reachable": is_reachable,
                "eligible": is_configured and is_reachable,
                "selected": last_run.get("selected", False),
                "attempted": last_run.get("attempted", False),
                "succeeded": last_run.get("succeeded", False),
                "failed": last_run.get("failed", False),
                "fallback": last_run.get("fallback", False),
                "executed": last_run.get("executed", False),
                "reason": reason,
                "last_model": active_model,
                "last_latency_ms": last_run.get("latency_ms") or (ping_ms if is_reachable else 999.0),
            }
        return matrix


# Global model gateway instance
default_model_gateway = ModelGateway()

