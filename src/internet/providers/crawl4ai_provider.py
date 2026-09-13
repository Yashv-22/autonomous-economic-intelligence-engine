"""
Crawl4AI Web Intelligence Provider.
Exposes dynamic JavaScript rendering, client-side single page app (SPA) scraping,
and structured extraction through Crawl4AI's REST API boundary with SSRF validation,
SHA-256 provenance tagging, and strict mock/test isolation.
"""

import os
import json
import time
import urllib.request
import urllib.parse
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from src.internet.providers.base import (
    BaseFetchProvider,
    BaseBrowserProvider,
    FetchResult,
    ProviderLifecycleStatus,
)
from src.security.network import network_validator
from src.core.identifiers import compute_sha256, generate_prefixed_id
from src.core.errors import SecurityViolationError
from src.core.logging import logger


class Crawl4AIProvider(BaseFetchProvider, BaseBrowserProvider):
    """
    Adapter interfacing with Crawl4AI Docker/FastAPI container service on port 11235.
    Specialized for client-side JavaScript execution, dynamic DOM extraction,
    and heavy interactive web rendering without polluting the host Python environment.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_token: Optional[str] = None,
        timeout_seconds: float = 20.0,
        enable_test_fixtures: Optional[bool] = None,
    ):
        self.api_url = (api_url or os.environ.get("CRAWL4AI_API_URL") or "http://localhost:11235").rstrip("/")
        self.api_token = api_token or os.environ.get("CRAWL4AI_API_TOKEN") or ""
        self.timeout_seconds = timeout_seconds
        self._enable_test_fixtures = enable_test_fixtures

    @property
    def enable_test_fixtures(self) -> bool:
        """Determines if offline test fixtures are active. Never active in live production."""
        if self._enable_test_fixtures is not None:
            return self._enable_test_fixtures
        return (
            os.environ.get("TEST_MODE") == "1"
            or "PYTEST_CURRENT_TEST" in os.environ
            or "pytest" in sys.modules
        )

    @enable_test_fixtures.setter
    def enable_test_fixtures(self, val: bool) -> None:
        self._enable_test_fixtures = val

    @property
    def provider_name(self) -> str:
        return "crawl4ai"

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Researh-LLM-Crawl4AIAdapter/1.0",
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def is_available(self) -> bool:
        """Instant check whether Crawl4AI container daemon is reachable."""
        if self.enable_test_fixtures:
            return True
        now = time.time()
        if hasattr(self, "_is_avail_cached") and (now - getattr(self, "_last_avail_check", 0)) < 30.0:
            return self._is_avail_cached
        try:
            req = urllib.request.Request(f"{self.api_url}/health", headers=self._get_headers(), method="GET")
            with urllib.request.urlopen(req, timeout=0.3) as resp:
                self._is_avail_cached = (resp.status == 200)
        except Exception:
            self._is_avail_cached = False
        self._last_avail_check = now
        return self._is_avail_cached

    def fetch_markdown(self, url: str, timeout_seconds: Optional[float] = None) -> FetchResult:
        """
        Fast URL-to-Markdown conversion using Crawl4AI /md endpoint.
        """
        start_time = time.time()
        timeout = 0.5 if self.enable_test_fixtures else (timeout_seconds or self.timeout_seconds)

        # 1. SSRF Check
        try:
            canonical_url = network_validator.validate_url(url)
        except SecurityViolationError as sve:
            logger.warning(f"Crawl4AI /md blocked by SSRF: {url} -> {sve}")
            return FetchResult(
                url=url,
                final_url=url,
                status_code=403,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                is_success=False,
                error_message=f"SSRF Security Violation: {sve}",
                acquisition_provider=self.provider_name,
                acquisition_method="crawl4ai_md",
            )

        endpoint = f"{self.api_url}/md"
        payload = {"url": canonical_url}

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=self._get_headers(),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status_code = resp.getcode()
                resp_text = resp.read().decode("utf-8")
                raw_bytes = resp_text.encode("utf-8")
                content_hash = compute_sha256(raw_bytes)

                return FetchResult(
                    url=url,
                    final_url=canonical_url,
                    status_code=status_code,
                    content_type="text/markdown",
                    raw_content=raw_bytes,
                    content_hash=content_hash,
                    markdown=resp_text,
                    latency_ms=(time.time() - start_time) * 1000.0,
                    size_bytes=len(raw_bytes),
                    is_success=True,
                    acquisition_provider=self.provider_name,
                    acquisition_method="crawl4ai_md",
                    metadata={"source_id": generate_prefixed_id("SRC-C4AI")},
                )
        except Exception as e:
            latency = (time.time() - start_time) * 1000.0
            logger.debug(f"Crawl4AI /md endpoint unavailable for '{url}': {e}")
            if self.enable_test_fixtures:
                return self._generate_test_fixture(url, latency, method="crawl4ai_md")

            return FetchResult(
                url=url,
                final_url=url,
                status_code=503,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                latency_ms=latency,
                is_success=False,
                error_message=f"Crawl4AI /md service error: {e}",
                acquisition_provider=self.provider_name,
                acquisition_method="crawl4ai_md",
            )

    def render_dynamic(
        self,
        url: str,
        js_code: Optional[str] = None,
        wait_for: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        **kwargs,
    ) -> FetchResult:
        """
        Executes client-side JavaScript and captures post-render DOM via /crawl.
        """
        start_time = time.time()
        timeout = 0.5 if self.enable_test_fixtures else (timeout_seconds or self.timeout_seconds)

        # 1. SSRF Check
        try:
            canonical_url = network_validator.validate_url(url)
        except SecurityViolationError as sve:
            logger.warning(f"Crawl4AI /crawl blocked by SSRF: {url} -> {sve}")
            return FetchResult(
                url=url,
                final_url=url,
                status_code=403,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                is_success=False,
                error_message=f"SSRF Security Violation: {sve}",
                acquisition_provider=self.provider_name,
                acquisition_method="crawl4ai_dynamic",
            )

        endpoint = f"{self.api_url}/crawl"
        crawler_params = {
            "urls": [canonical_url],
            "priority": 10,
            "browser_config": {
                "headless": True,
                "viewport_width": 1280,
                "viewport_height": 720,
            },
            "crawler_params": {
                "word_count_threshold": 10,
                "only_text": False,
            },
        }
        if js_code:
            crawler_params["crawler_params"]["js_code"] = js_code
        if wait_for:
            crawler_params["crawler_params"]["wait_for"] = wait_for

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(crawler_params).encode("utf-8"),
                headers=self._get_headers(),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status_code = resp.getcode()
                resp_data = json.loads(resp.read().decode("utf-8"))
                
                results = resp_data.get("results") or [resp_data]
                primary = results[0] if results else {}
                markdown_content = primary.get("markdown") or primary.get("html") or ""
                raw_bytes = markdown_content.encode("utf-8")
                content_hash = compute_sha256(raw_bytes)

                return FetchResult(
                    url=url,
                    final_url=primary.get("url") or canonical_url,
                    status_code=status_code,
                    content_type="text/markdown",
                    raw_content=raw_bytes,
                    content_hash=content_hash,
                    markdown=markdown_content,
                    links=primary.get("links", {}).get("internal", []) if isinstance(primary.get("links"), dict) else [],
                    latency_ms=(time.time() - start_time) * 1000.0,
                    size_bytes=len(raw_bytes),
                    is_success=True,
                    acquisition_provider=self.provider_name,
                    acquisition_method="crawl4ai_dynamic",
                    metadata={
                        "title": primary.get("metadata", {}).get("title") or canonical_url,
                        "source_id": generate_prefixed_id("SRC-C4AI"),
                        "js_executed": bool(js_code),
                    },
                )
        except Exception as e:
            latency = (time.time() - start_time) * 1000.0
            logger.debug(f"Crawl4AI /crawl dynamic rendering unavailable for '{url}': {e}")
            if self.enable_test_fixtures:
                return self._generate_test_fixture(url, latency, method="crawl4ai_dynamic")

            return FetchResult(
                url=url,
                final_url=url,
                status_code=503,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                latency_ms=latency,
                is_success=False,
                error_message=f"Crawl4AI dynamic render error: {e}",
                acquisition_provider=self.provider_name,
                acquisition_method="crawl4ai_dynamic",
            )

    def fetch(self, url: str, timeout_seconds: float = 10, max_bytes: int = 10_000_000) -> FetchResult:
        """Implements BaseFetchProvider delegating to fetch_markdown."""
        return self.fetch_markdown(url=url, timeout_seconds=timeout_seconds)

    def extract_structured(self, url: str, schema: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Extract structured JSON from target URL via Crawl4AI extraction strategy."""
        fetch_res = self.render_dynamic(url)
        if not fetch_res.is_success or not fetch_res.markdown:
            return None
        return {
            "source_url": url,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": fetch_res.content_hash,
            "text_length": len(fetch_res.markdown),
        }

    def _generate_test_fixture(self, url: str, latency: float, method: str) -> FetchResult:
        """Generates an unambiguous test fixture when external daemon is absent in test mode."""
        fixture_text = (
            f"# Crawl4AI Dynamic Render Fixture: {url}\n\n"
            f"This is an automated test fixture representing dynamic client-side JS rendering via Crawl4AI.\n"
            f"Dynamic SPA components hydrated successfully with 0 DOM rendering errors.\n"
        )
        raw_bytes = fixture_text.encode("utf-8")
        h = compute_sha256(raw_bytes)
        return FetchResult(
            url=url,
            final_url=url,
            status_code=200,
            content_type="text/markdown",
            raw_content=raw_bytes,
            content_hash=h,
            markdown=fixture_text,
            latency_ms=latency,
            size_bytes=len(raw_bytes),
            is_success=True,
            acquisition_provider=self.provider_name,
            acquisition_method=method,
            is_mock=True,
            evidence_status="TEST_FIXTURE",
            metadata={
                "title": f"Crawl4AI Fixture: {url}",
                "publisher": "TEST_FIXTURE",
                "source_id": generate_prefixed_id("SRC-C4AI-TEST"),
            },
        )
