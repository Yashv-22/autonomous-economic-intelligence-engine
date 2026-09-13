"""
Adaptive Acquisition Router.
Evaluates research requirements, provider capabilities, and runtime availability to
route acquisition requests intelligently with truthful failure and fallback tracking.
"""

import os
import time
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.internet.providers.base import (
    FetchResult,
    BaseFetchProvider,
    ProviderLifecycleStatus,
)
from src.internet.fetcher.fetcher import WebFetcher
from src.internet.providers.agent_reach_provider import AgentReachFetchProvider
from src.internet.providers.firecrawl_provider import FirecrawlProvider
from src.internet.providers.crawl4ai_provider import Crawl4AIProvider
from src.security.network import network_validator
from src.security.sanitizer import ContentSanitizer
from src.core.identifiers import compute_sha256
from src.core.errors import SecurityViolationError
from src.core.events import default_event_bus, SystemEvent
from src.core.logging import logger


class AcquisitionRequirement(BaseModel):
    """Specifies the technical and epistemic requirements for acquiring a resource."""
    url: str
    capability: str = "fetch"  # fetch, scrape, render_dynamic, crawl, map
    needs_javascript: bool = False
    deep_crawl: bool = False
    map_topology: bool = False
    timeout_seconds: float = 10.0
    research_run_id: Optional[str] = None
    investigation_id: Optional[str] = None
    tool_call_id: Optional[str] = None


class AcquisitionAuditRecord(BaseModel):
    """Comprehensive, credential-free audit log of an acquisition attempt."""
    source_id: str
    canonical_url: str
    selected_provider: str
    attempted_providers: List[str] = Field(default_factory=list)
    executed_provider: Optional[str] = None
    capability: str
    lifecycle: ProviderLifecycleStatus
    status_code: int = 0
    latency_ms: float = 0.0
    is_success: bool = False
    failure_reason: Optional[str] = None
    fallback_path: List[str] = Field(default_factory=list)
    research_run_id: Optional[str] = None
    investigation_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AdaptiveAcquisitionRouter:
    """
    Intelligent decision engine routing acquisition requests to the most appropriate provider.
    Enforces SSRF defense, prompt injection sanitization, canonical source identity,
    and truthful provider lifecycle logging.
    """

    def __init__(
        self,
        native_fetcher: Optional[WebFetcher] = None,
        agent_reach_fetcher: Optional[AgentReachFetchProvider] = None,
        crawl4ai_provider: Optional[Crawl4AIProvider] = None,
        firecrawl_provider: Optional[FirecrawlProvider] = None,
    ):
        self.native_fetcher = native_fetcher or WebFetcher()
        self.agent_reach_fetcher = agent_reach_fetcher or AgentReachFetchProvider()
        self.crawl4ai = crawl4ai_provider or Crawl4AIProvider()
        self.firecrawl = firecrawl_provider or FirecrawlProvider()
        self._cache: Dict[str, Tuple[float, FetchResult]] = {}

    def get_canonical_source_id(self, url: str) -> str:
        """
        Derives an immutable, canonical logical source ID from the normalized URL.
        Different providers acquiring the same URL map to the same logical source.
        """
        parsed = urllib.parse.urlparse(url)
        norm_url = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path.rstrip('/')}"
        if parsed.query:
            norm_url += f"?{parsed.query}"
        h = compute_sha256(norm_url.encode("utf-8"))
        return f"SRC-{h[:12].upper()}"

    def fetch(self, url: str, timeout_seconds: float = 10.0, **kwargs) -> FetchResult:
        """Conforms to BaseFetchProvider interface for universal pluggability across research engines."""
        req = AcquisitionRequirement(url=url, timeout_seconds=timeout_seconds)
        res, _ = self.route_acquisition(req)
        return res

    def route_acquisition(self, req: AcquisitionRequirement) -> Tuple[FetchResult, AcquisitionAuditRecord]:
        """
        Executes capability-driven acquisition following a truthful decision model:
          1. Check SSRF & network security first.
          2. Select most suitable provider based on requirements (dynamic JS vs static vs map/crawl).
          3. Truthfully record lifecycle: selected -> attempted -> succeeded/failed -> fallback.
          4. Sanitize content and register canonical provenance.
        """
        start_time = time.time()
        source_id = self.get_canonical_source_id(req.url)

        audit = AcquisitionAuditRecord(
            source_id=source_id,
            canonical_url=req.url,
            selected_provider="native_fetcher",
            capability=req.capability,
            lifecycle=ProviderLifecycleStatus.CONFIGURED,
            research_run_id=req.research_run_id,
            investigation_id=req.investigation_id,
        )

        # 1. SSRF & Scheme Security Verification
        try:
            canonical_url = network_validator.validate_url(req.url)
            audit.canonical_url = canonical_url
            audit.lifecycle = ProviderLifecycleStatus.ELIGIBLE
        except SecurityViolationError as sve:
            logger.warning(f"Router: Blocked URL '{req.url}' by SSRF security policy: {sve}")
            audit.lifecycle = ProviderLifecycleStatus.FAILED
            audit.failure_reason = f"SSRF Violation: {sve}"
            res = FetchResult(
                url=req.url,
                final_url=req.url,
                status_code=403,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                is_success=False,
                error_message=audit.failure_reason,
                acquisition_provider="security_guard",
                acquisition_method="blocked_ssrf",
            )
            self._emit_telemetry(audit)
            return res, audit

        # 1b. Fast Cache Check (TTL: 600s)
        cache_key = f"{req.capability}:{canonical_url}"
        if cache_key in self._cache:
            cached_time, cached_res = self._cache[cache_key]
            if time.time() - cached_time < 600.0:
                logger.debug(f"Router: In-memory cache hit for '{canonical_url}'")
                audit.selected_provider = "cache"
                audit.executed_provider = (cached_res.metadata or {}).get("executed_provider") or cached_res.acquisition_provider or "cache"
                audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
                audit.status_code = cached_res.status_code
                audit.latency_ms = (time.time() - start_time) * 1000.0
                audit.is_success = True
                self._emit_telemetry(audit)
                return cached_res, audit

        # 2. Decision Model: Select Provider Chain
        # Path 0: High-fidelity scrape explicitly requested (e.g. scrape_page tool)
        if req.capability == "scrape":
            return self._execute_scrape_chain(canonical_url, req, audit, start_time)

        # Path A: Dynamic JavaScript or Single Page App explicitly requested
        if req.needs_javascript or req.capability == "render_dynamic":
            return self._execute_dynamic_chain(canonical_url, req, audit, start_time)

        # Path B: Specialized platform channel (YouTube, RSS) handled by Agent Reach
        if self._is_agent_reach_specialty(canonical_url):
            return self._execute_agent_reach_chain(canonical_url, req, audit, start_time)

        # Path C: Standard static Web acquisition with intelligent fallback
        return self._execute_static_with_fallback(canonical_url, req, audit, start_time)

    def _is_agent_reach_specialty(self, url: str) -> bool:
        lower = url.lower()
        return (
            "youtube.com" in lower
            or "youtu.be" in lower
            or "/feed" in lower
            or "/rss" in lower
            or lower.endswith(".xml")
            or "atom" in lower
        )

    def _execute_dynamic_chain(
        self,
        url: str,
        req: AcquisitionRequirement,
        audit: AcquisitionAuditRecord,
        start_time: float,
    ) -> Tuple[FetchResult, AcquisitionAuditRecord]:
        """Routes dynamic JS requirements: Crawl4AI -> fallback Firecrawl -> fallback Native."""
        audit.selected_provider = "crawl4ai"
        audit.lifecycle = ProviderLifecycleStatus.SELECTED

        # Attempt 1: Crawl4AI
        audit.attempted_providers.append("crawl4ai")
        audit.lifecycle = ProviderLifecycleStatus.ATTEMPTED
        try:
            res = self.crawl4ai.render_dynamic(url, timeout_seconds=req.timeout_seconds)
            if res.is_success and res.raw_content:
                audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
                audit.executed_provider = "crawl4ai"
                audit.is_success = True
                audit.status_code = res.status_code
                audit.latency_ms = (time.time() - start_time) * 1000.0
                self._sanitize_and_tag(res, audit)
                return res, audit
            audit.failure_reason = res.error_message or "Crawl4AI empty response"
        except Exception as e:
            audit.failure_reason = str(e)

        logger.debug(f"Router: Crawl4AI failed for '{url}' ({audit.failure_reason}). Triggering Firecrawl fallback.")
        audit.fallback_path.append("firecrawl")

        # Attempt 2: Firecrawl Scrape Fallback
        audit.attempted_providers.append("firecrawl")
        audit.lifecycle = ProviderLifecycleStatus.FALLBACK
        try:
            res = self.firecrawl.scrape(url, timeout_seconds=req.timeout_seconds)
            if res.is_success and res.raw_content:
                audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
                audit.executed_provider = "firecrawl"
                audit.is_success = True
                audit.status_code = res.status_code
                audit.latency_ms = (time.time() - start_time) * 1000.0
                self._sanitize_and_tag(res, audit)
                return res, audit
            audit.failure_reason = res.error_message or "Firecrawl fallback failed"
        except Exception as e:
            audit.failure_reason = str(e)

        # Final failure
        audit.lifecycle = ProviderLifecycleStatus.FAILED
        audit.latency_ms = (time.time() - start_time) * 1000.0
        final_res = FetchResult(
            url=url,
            final_url=url,
            status_code=503,
            content_type="text/plain",
            raw_content=b"",
            content_hash=compute_sha256(b""),
            is_success=False,
            error_message=f"All dynamic providers failed: {audit.failure_reason}",
            acquisition_provider=audit.attempted_providers[-1] if audit.attempted_providers else "none",
            acquisition_method="failed_dynamic_chain",
        )
        self._emit_telemetry(audit)
        return final_res, audit

    def _execute_scrape_chain(
        self,
        url: str,
        req: AcquisitionRequirement,
        audit: AcquisitionAuditRecord,
        start_time: float,
    ) -> Tuple[FetchResult, AcquisitionAuditRecord]:
        """Routes explicit scrape capability: Firecrawl -> fallback Crawl4AI -> fallback Native."""
        audit.selected_provider = "firecrawl"
        audit.lifecycle = ProviderLifecycleStatus.SELECTED
        audit.attempted_providers.append("firecrawl")
        audit.lifecycle = ProviderLifecycleStatus.ATTEMPTED

        # Attempt 1: Firecrawl Scrape
        try:
            res = self.firecrawl.scrape(url, timeout_seconds=req.timeout_seconds)
            if res.is_success and res.raw_content:
                audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
                audit.executed_provider = "firecrawl"
                audit.is_success = True
                audit.status_code = res.status_code
                audit.latency_ms = (time.time() - start_time) * 1000.0
                self._sanitize_and_tag(res, audit)
                return res, audit
            audit.failure_reason = res.error_message or "Firecrawl scrape failed"
        except Exception as e:
            audit.failure_reason = str(e)

        # Attempt 2: Crawl4AI fallback
        audit.fallback_path.append("crawl4ai")
        audit.attempted_providers.append("crawl4ai")
        audit.lifecycle = ProviderLifecycleStatus.FALLBACK
        try:
            res = self.crawl4ai.fetch_markdown(url, timeout_seconds=req.timeout_seconds)
            if res.is_success and res.raw_content:
                audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
                audit.executed_provider = "crawl4ai"
                audit.is_success = True
                audit.status_code = res.status_code
                audit.latency_ms = (time.time() - start_time) * 1000.0
                self._sanitize_and_tag(res, audit)
                return res, audit
        except Exception as e:
            logger.debug(f"Router: Crawl4AI scrape fallback error: {e}")

        # Attempt 3: Native fallback
        audit.fallback_path.append("native_fetcher")
        audit.attempted_providers.append("native_fetcher")
        res = self.native_fetcher.fetch(url, timeout_seconds=req.timeout_seconds)
        if res.is_success and res.raw_content:
            audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
            audit.executed_provider = "native_fetcher"
            audit.is_success = True
            audit.status_code = res.status_code
            audit.latency_ms = (time.time() - start_time) * 1000.0
            self._sanitize_and_tag(res, audit)
            return res, audit

        audit.lifecycle = ProviderLifecycleStatus.FAILED
        audit.latency_ms = (time.time() - start_time) * 1000.0
        self._emit_telemetry(audit)
        return res, audit

    def _execute_agent_reach_chain(
        self,
        url: str,
        req: AcquisitionRequirement,
        audit: AcquisitionAuditRecord,
        start_time: float,
    ) -> Tuple[FetchResult, AcquisitionAuditRecord]:
        """Routes platform-specific content (YouTube, RSS) to Agent Reach."""
        audit.selected_provider = "agent_reach"
        audit.lifecycle = ProviderLifecycleStatus.SELECTED
        audit.attempted_providers.append("agent_reach")
        audit.lifecycle = ProviderLifecycleStatus.ATTEMPTED

        try:
            res = self.agent_reach_fetcher.fetch(url, timeout_seconds=req.timeout_seconds)
            if res.is_success and res.raw_content:
                audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
                audit.executed_provider = "agent_reach"
                audit.is_success = True
                audit.status_code = res.status_code
                audit.latency_ms = (time.time() - start_time) * 1000.0
                self._sanitize_and_tag(res, audit)
                return res, audit
            audit.failure_reason = res.error_message or "Agent Reach failed"
        except Exception as e:
            audit.failure_reason = str(e)

        # Fallback to native fetcher
        audit.fallback_path.append("native_fetcher")
        audit.attempted_providers.append("native_fetcher")
        audit.lifecycle = ProviderLifecycleStatus.FALLBACK
        res = self.native_fetcher.fetch(url, timeout_seconds=req.timeout_seconds)
        if res.is_success and res.raw_content:
            audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
            audit.executed_provider = "native_fetcher"
            audit.is_success = True
            audit.status_code = res.status_code
            audit.latency_ms = (time.time() - start_time) * 1000.0
            self._sanitize_and_tag(res, audit)
            return res, audit

        audit.lifecycle = ProviderLifecycleStatus.FAILED
        audit.latency_ms = (time.time() - start_time) * 1000.0
        self._emit_telemetry(audit)
        return res, audit

    def _execute_static_with_fallback(
        self,
        url: str,
        req: AcquisitionRequirement,
        audit: AcquisitionAuditRecord,
        start_time: float,
    ) -> Tuple[FetchResult, AcquisitionAuditRecord]:
        """Routes standard static fetch with intelligent escalation if blocked or JS-shell detected."""
        audit.selected_provider = "native_fetcher"
        audit.lifecycle = ProviderLifecycleStatus.SELECTED
        audit.attempted_providers.append("native_fetcher")
        audit.lifecycle = ProviderLifecycleStatus.ATTEMPTED

        # 1. Native HTTP Fetch (Ultra-fast static path)
        try:
            res = self.native_fetcher.fetch(url, timeout_seconds=req.timeout_seconds)
        except Exception as e:
            res = FetchResult(
                url=url, final_url=url, status_code=500, content_type="text/plain",
                raw_content=b"", content_hash=compute_sha256(b""), is_success=False, error_message=str(e),
            )

        # Inspect if static fetch succeeded and contains substantive HTML/text
        if res.is_success and res.raw_content and not self._is_js_shell(res):
            audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
            audit.executed_provider = "native_fetcher"
            audit.is_success = True
            audit.status_code = res.status_code
            audit.latency_ms = (time.time() - start_time) * 1000.0
            res.acquisition_provider = "native_fetcher"
            res.acquisition_method = "native_http"
            self._sanitize_and_tag(res, audit)
            return res, audit

        # 2. If blocked (403/Cloudflare) or JS shell -> Escalate to Crawl4AI if available
        if hasattr(self.crawl4ai, "is_available") and not self.crawl4ai.is_available():
            logger.debug("Router: Crawl4AI daemon offline, skipping directly to next fallback.")
        else:
            logger.debug(f"Router: Static fetch insufficient for '{url}' (status={res.status_code}). Escalating to Crawl4AI.")
            audit.fallback_path.append("crawl4ai")
            audit.attempted_providers.append("crawl4ai")
            audit.lifecycle = ProviderLifecycleStatus.FALLBACK

            try:
                c4_res = self.crawl4ai.fetch_markdown(url, timeout_seconds=req.timeout_seconds)
                if c4_res.is_success and c4_res.raw_content:
                    audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
                    audit.executed_provider = "crawl4ai"
                    audit.is_success = True
                    audit.status_code = c4_res.status_code
                    audit.latency_ms = (time.time() - start_time) * 1000.0
                    self._sanitize_and_tag(c4_res, audit)
                    return c4_res, audit
            except Exception as e:
                logger.debug(f"Router: Crawl4AI fallback error: {e}")

        # 3. If Crawl4AI unavailable or blocked -> Escalate to Firecrawl if available
        if hasattr(self.firecrawl, "is_available") and not self.firecrawl.is_available():
            logger.debug("Router: Firecrawl daemon offline, skipping directly to next fallback.")
        else:
            logger.debug(f"Router: Escalating to Firecrawl for '{url}'.")
            audit.fallback_path.append("firecrawl")
            audit.attempted_providers.append("firecrawl")

            try:
                fc_res = self.firecrawl.scrape(url, timeout_seconds=req.timeout_seconds)
                if fc_res.is_success and fc_res.raw_content:
                    audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
                    audit.executed_provider = "firecrawl"
                    audit.is_success = True
                    audit.status_code = fc_res.status_code
                    audit.latency_ms = (time.time() - start_time) * 1000.0
                    self._sanitize_and_tag(fc_res, audit)
                    return fc_res, audit
            except Exception as e:
                logger.debug(f"Router: Firecrawl fallback error: {e}")

        # 4. If Crawl4AI and Firecrawl daemons are offline -> Escalate to Agent Reach (Jina Reader)
        logger.debug(f"Router: Escalating to Agent Reach for '{url}'.")
        audit.fallback_path.append("agent_reach")
        audit.attempted_providers.append("agent_reach")

        try:
            ar_res = self.agent_reach_fetcher.fetch(url, timeout_seconds=req.timeout_seconds)
            if ar_res.is_success and ar_res.raw_content:
                audit.lifecycle = ProviderLifecycleStatus.SUCCEEDED
                audit.executed_provider = "agent_reach"
                audit.is_success = True
                audit.status_code = ar_res.status_code
                audit.latency_ms = (time.time() - start_time) * 1000.0
                ar_res.acquisition_provider = "agent_reach"
                ar_res.acquisition_method = "agent_reach_jina"
                self._sanitize_and_tag(ar_res, audit)
                return ar_res, audit
        except Exception as e:
            logger.debug(f"Router: Agent Reach fallback error: {e}")

        # If original static result had any content, return it as partial, else fail
        audit.lifecycle = ProviderLifecycleStatus.FAILED
        audit.latency_ms = (time.time() - start_time) * 1000.0
        audit.failure_reason = "All static and fallback providers failed or returned empty content"
        self._emit_telemetry(audit)
        return res, audit

    def _is_js_shell(self, res: FetchResult) -> bool:
        """Heuristic detecting client-side SPA shells requiring dynamic browser rendering."""
        if not res.raw_content:
            return True
        # If explicitly not HTML, don't treat as JS shell
        if res.content_type and "html" not in res.content_type.lower():
            return False
        text = res.raw_content[:2000].decode("utf-8", errors="replace").lower()
        js_indicators = [
            "you need to enable javascript to run this app",
            "please enable javascript",
            "<noscript>",
            "enable javascript and refresh",
            'id="root"></div>',
            'id="app"></div>',
        ]
        return any(ind in text for ind in js_indicators)

    def _sanitize_and_tag(self, res: FetchResult, audit: AcquisitionAuditRecord) -> None:
        """Sanitizes untrusted text and attaches canonical source identity metadata."""
        if res.raw_content:
            text = res.raw_content.decode("utf-8", errors="replace")
            is_inj, _ = ContentSanitizer.detect_prompt_injection(text)
            if is_inj:
                logger.warning(f"Router: Prompt injection detected in '{res.url}'. Sanitizing untrusted text.")
                cleaned_text = ContentSanitizer.sanitize_untrusted_text(text)
                res.raw_content = cleaned_text.encode("utf-8")
                res.content_hash = compute_sha256(res.raw_content)
                if res.markdown:
                    res.markdown = cleaned_text

        # Ensure metadata has source_id and provider info
        if res.metadata is None:
            res.metadata = {}
        res.metadata["canonical_source_id"] = audit.source_id
        res.metadata["executed_provider"] = audit.executed_provider or res.acquisition_provider
        
        # Cache successful substantive fetch result
        if res.is_success and res.raw_content:
            cache_key = f"{audit.capability}:{audit.canonical_url}"
            self._cache[cache_key] = (time.time(), res)

        self._emit_telemetry(audit)

    def _emit_telemetry(self, audit: AcquisitionAuditRecord) -> None:
        """Publishes acquisition telemetry event without recording credentials."""
        try:
            default_event_bus.publish(
                SystemEvent(
                    event_type="ACQUISITION_TELEMETRY",
                    correlation_id=audit.research_run_id or "NONE",
                    payload={
                        "source_id": audit.source_id,
                        "url": audit.canonical_url,
                        "selected_provider": audit.selected_provider,
                        "executed_provider": audit.executed_provider,
                        "lifecycle": audit.lifecycle.value,
                        "status_code": audit.status_code,
                        "latency_ms": audit.latency_ms,
                        "is_success": audit.is_success,
                        "fallback_path": audit.fallback_path,
                    },
                    agent_id=f"acquisition:{audit.executed_provider or audit.selected_provider}",
                )
            )
        except Exception as e:
            logger.debug(f"Router: Telemetry emit skipped: {e}")
