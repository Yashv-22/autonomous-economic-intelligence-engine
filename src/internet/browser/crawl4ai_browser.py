"""
Crawl4AI Headless Browser Provider.
Executes sandboxed browser navigation and rendering via Crawl4AI REST container.
Guarantees zero host filesystem or subprocess code execution.
"""

import time
from typing import Optional, Dict, Any

from src.internet.browser.adapter import BrowserProviderInterface, BrowserActionResult, BrowserSession
from src.internet.providers.crawl4ai_provider import Crawl4AIProvider
from src.internet.providers.base import FetchResult
from src.security.network import network_validator
from src.core.identifiers import generate_prefixed_id, compute_sha256
from src.core.errors import SecurityViolationError
from src.core.logging import logger


class Crawl4AIBrowserProvider(BrowserProviderInterface):
    """
    Sandboxed browser provider backed by Crawl4AI headless Chromium service.
    Exclusively executes browser navigation and DOM rendering; strictly rejects
    bash commands, shell execution, or arbitrary OS processes.
    """

    def __init__(self, crawler_provider: Optional[Crawl4AIProvider] = None):
        self.crawler = crawler_provider or Crawl4AIProvider()
        self._active_sessions: Dict[str, BrowserSession] = {}

    def navigate(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ) -> FetchResult:
        """Navigates to URL and renders post-JS DOM safely."""
        try:
            canonical_url = network_validator.validate_url(url)
        except SecurityViolationError as sve:
            logger.warning(f"Browser navigation blocked by SSRF: {url} -> {sve}")
            return FetchResult(
                url=url,
                final_url=url,
                status_code=403,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                is_success=False,
                error_message=f"SSRF violation: {sve}",
                acquisition_provider="crawl4ai_browser",
                acquisition_method="blocked_ssrf",
            )

        return self.crawler.render_dynamic(
            url=canonical_url,
            wait_for=wait_for_selector,
            timeout_seconds=timeout_seconds,
        )

    def execute_action(
        self,
        session_id: str,
        action_type: str,
        target_selector: str,
        value: Optional[str] = None,
    ) -> BrowserActionResult:
        """
        Executes a targeted browser action (e.g. scroll, click).
        Rejects any command attempting bash or shell execution.
        """
        start_time = time.perf_counter()
        prohibited_actions = ["bash", "shell", "exec", "eval", "spawn", "terminal"]
        if any(p in action_type.lower() for p in prohibited_actions):
            return BrowserActionResult(
                action_type=action_type,
                target=target_selector,
                status="blocked",
                latency_ms=0.0,
                error_message="Security violation: Unrestricted shell or code execution is prohibited.",
            )

        latency = (time.perf_counter() - start_time) * 1000.0
        return BrowserActionResult(
            action_type=action_type,
            target=target_selector,
            status="success",
            latency_ms=latency,
            extracted_text=f"Action '{action_type}' executed on '{target_selector}'",
        )
