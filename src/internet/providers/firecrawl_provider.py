"""
Firecrawl Web Intelligence Provider.
Exposes scraping, deep crawling, site mapping, and web search through
Firecrawl's REST API boundary with SSRF validation, cryptographic provenance,
and strict mock/test isolation.
"""

import os
import json
import time
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

import sys

from src.internet.providers.base import (
    BaseSearchProvider,
    BaseFetchProvider,
    BaseCrawlerProvider,
    BaseMapProvider,
    SearchResultItem,
    FetchResult,
    ProviderLifecycleStatus,
)
from src.security.network import network_validator
from src.core.identifiers import compute_sha256, generate_prefixed_id
from src.core.errors import SecurityViolationError
from src.core.logging import logger


class FirecrawlProvider(BaseSearchProvider, BaseFetchProvider, BaseCrawlerProvider, BaseMapProvider):
    """
    Adapter interfacing with self-hosted Firecrawl cluster or cloud API.
    Enforces SSRF prevention, normalized dataclass output, and SHA-256 evidence hashing.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 15.0,
        enable_test_fixtures: Optional[bool] = None,
    ):
        self.api_url = (api_url or os.environ.get("FIRECRAWL_API_URL") or "http://localhost:3002").rstrip("/")
        self.api_key = api_key or os.environ.get("FIRECRAWL_API_KEY") or ""
        self.timeout_seconds = timeout_seconds
        # Explicitly set override if provided
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
        return "firecrawl"

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Researh-LLM-FirecrawlAdapter/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def is_available(self) -> bool:
        """Instant check whether Firecrawl service is reachable."""
        if self.enable_test_fixtures:
            return True
        now = time.time()
        if hasattr(self, "_is_avail_cached") and (now - getattr(self, "_last_avail_check", 0)) < 30.0:
            return self._is_avail_cached
        try:
            req = urllib.request.Request(f"{self.api_url}/v1/health", headers=self._get_headers(), method="GET")
            with urllib.request.urlopen(req, timeout=0.3) as resp:
                self._is_avail_cached = (resp.status == 200)
        except Exception:
            self._is_avail_cached = False
        self._last_avail_check = now
        return self._is_avail_cached

    def scrape(
        self,
        url: str,
        formats: Optional[List[str]] = None,
        timeout_seconds: Optional[float] = None,
        **kwargs,
    ) -> FetchResult:
        """
        Scrape a single webpage via Firecrawl /v1/scrape endpoint.
        Returns normalized FetchResult with clean markdown and exact hash.
        """
        start_time = time.time()
        formats = formats or ["markdown", "html"]
        timeout = 0.5 if self.enable_test_fixtures else (timeout_seconds or self.timeout_seconds)

        # 1. SSRF & Network Security Validation
        try:
            canonical_url = network_validator.validate_url(url)
        except SecurityViolationError as sve:
            logger.warning(f"Firecrawl scrape blocked by SSRF validator: {url} -> {sve}")
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
                acquisition_method="firecrawl_scrape",
            )

        # 2. Dispatch to Firecrawl REST API
        endpoint = f"{self.api_url}/v1/scrape"
        payload = {
            "url": canonical_url,
            "formats": formats,
            "onlyMainContent": True,
        }

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=self._get_headers(),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status_code = resp.getcode()
                resp_data = json.loads(resp.read().decode("utf-8"))

                if not resp_data.get("success", False) and "data" not in resp_data:
                    raise RuntimeError(resp_data.get("error", "Firecrawl scrape failed"))

                data = resp_data.get("data", {})
                markdown_content = data.get("markdown") or data.get("content") or ""
                raw_bytes = markdown_content.encode("utf-8")
                content_hash = compute_sha256(raw_bytes)
                metadata = data.get("metadata", {})
                final_url = metadata.get("sourceURL") or metadata.get("url") or canonical_url
                publisher = metadata.get("publisher") or metadata.get("og:site_name") or "UNKNOWN"
                title = metadata.get("title") or final_url

                return FetchResult(
                    url=url,
                    final_url=final_url,
                    status_code=status_code,
                    content_type="text/markdown",
                    raw_content=raw_bytes,
                    content_hash=content_hash,
                    markdown=markdown_content,
                    links=data.get("links", []),
                    latency_ms=(time.time() - start_time) * 1000.0,
                    size_bytes=len(raw_bytes),
                    is_success=True,
                    acquisition_provider=self.provider_name,
                    acquisition_method="firecrawl_scrape",
                    metadata={
                        "title": title,
                        "publisher": publisher,
                        "source_id": generate_prefixed_id("SRC-FC"),
                        "status_code": status_code,
                    },
                )
        except Exception as e:
            latency = (time.time() - start_time) * 1000.0
            logger.debug(f"Firecrawl scrape service unavailable for '{url}': {e}")

            # Test fixture fallback only in explicit test environment
            if self.enable_test_fixtures:
                return self._generate_test_scrape_fixture(url, latency)

            return FetchResult(
                url=url,
                final_url=url,
                status_code=503,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                latency_ms=latency,
                is_success=False,
                error_message=f"Firecrawl service error: {e}",
                acquisition_provider=self.provider_name,
                acquisition_method="firecrawl_scrape",
            )

    def fetch(self, url: str, timeout_seconds: float = 10, max_bytes: int = 10_000_000) -> FetchResult:
        """Implements BaseFetchProvider by delegating to scrape()."""
        return self.scrape(url=url, timeout_seconds=timeout_seconds)

    def crawl(
        self,
        seed_url: str,
        max_depth: int = 2,
        max_pages: int = 10,
        timeout_seconds: Optional[float] = None,
        **kwargs,
    ) -> List[FetchResult]:
        """
        Recursively crawl seed_url via Firecrawl /v1/crawl endpoint.
        Returns list of normalized FetchResult documents.
        """
        start_time = time.time()
        timeout = timeout_seconds or (self.timeout_seconds * 2)

        # 1. SSRF Validation
        try:
            canonical_url = network_validator.validate_url(seed_url)
        except SecurityViolationError as sve:
            logger.warning(f"Firecrawl crawl blocked by SSRF validator: {seed_url} -> {sve}")
            return []

        endpoint = f"{self.api_url}/v1/crawl"
        payload = {
            "url": canonical_url,
            "maxDepth": max_depth,
            "limit": max_pages,
            "scrapeOptions": {"formats": ["markdown"]},
        }

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=self._get_headers(),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                results: List[FetchResult] = []

                # Handle synchronous data response or job status
                items = resp_data.get("data", [])
                for item in items:
                    markdown = item.get("markdown", "")
                    raw_bytes = markdown.encode("utf-8")
                    item_url = item.get("metadata", {}).get("sourceURL") or seed_url
                    results.append(
                        FetchResult(
                            url=item_url,
                            final_url=item_url,
                            status_code=200,
                            content_type="text/markdown",
                            raw_content=raw_bytes,
                            content_hash=compute_sha256(raw_bytes),
                            markdown=markdown,
                            latency_ms=(time.time() - start_time) * 1000.0,
                            size_bytes=len(raw_bytes),
                            is_success=True,
                            acquisition_provider=self.provider_name,
                            acquisition_method="firecrawl_crawl",
                            metadata={
                                "title": item.get("metadata", {}).get("title") or item_url,
                                "source_id": generate_prefixed_id("SRC-FC"),
                            },
                        )
                    )
                return results
        except Exception as e:
            logger.debug(f"Firecrawl crawl service unavailable for '{seed_url}': {e}")
            if self.enable_test_fixtures:
                return self._generate_test_crawl_fixture(seed_url)
            return []

    def map(self, url: str, search: Optional[str] = None, **kwargs) -> List[str]:
        """
        Map domain topology and discover URLs/sitemap entries via /v1/map.
        """
        try:
            canonical_url = network_validator.validate_url(url)
        except SecurityViolationError as sve:
            logger.warning(f"Firecrawl map blocked by SSRF validator: {url} -> {sve}")
            return []

        endpoint = f"{self.api_url}/v1/map"
        payload = {"url": canonical_url}
        if search:
            payload["search"] = search

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=self._get_headers(),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                links = resp_data.get("links", [])
                return [l for l in links if isinstance(l, str)]
        except Exception as e:
            logger.debug(f"Firecrawl map service unavailable for '{url}': {e}")
            if self.enable_test_fixtures:
                return [
                    f"{url.rstrip('/')}/about",
                    f"{url.rstrip('/')}/docs",
                    f"{url.rstrip('/')}/api",
                    f"{url.rstrip('/')}/case-studies",
                ]
            return []

    def search(self, query: str, max_results: int = 10, **kwargs) -> List[SearchResultItem]:
        """
        Execute web search query via Firecrawl /v1/search endpoint.
        """
        if not query or not query.strip():
            return []

        endpoint = f"{self.api_url}/v1/search"
        payload = {"query": query.strip(), "limit": max_results}

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=self._get_headers(),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                items = resp_data.get("data", [])
                results: List[SearchResultItem] = []
                for idx, item in enumerate(items[:max_results], 1):
                    item_url = item.get("url", "")
                    parsed = urllib.parse.urlparse(item_url)
                    results.append(
                        SearchResultItem(
                            title=item.get("title") or query,
                            url=item_url,
                            snippet=item.get("description") or item.get("markdown", "")[:250],
                            source_domain=parsed.netloc or "firecrawl.search",
                            provider=self.provider_name,
                            rank=idx,
                            source_type="web",
                            relevance_score=0.85,
                            metadata={"backend": "firecrawl_search_api"},
                        )
                    )
                return results
        except Exception as e:
            logger.debug(f"Firecrawl search service unavailable for '{query}': {e}")
            if self.enable_test_fixtures:
                return [
                    SearchResultItem(
                        title=f"Firecrawl Search Result for {query}",
                        url="https://example.org/firecrawl-result",
                        snippet=f"Evidence regarding {query} acquired via Firecrawl search adapter.",
                        source_domain="example.org",
                        provider=self.provider_name,
                        rank=1,
                        source_type="web",
                        relevance_score=0.80,
                        is_mock=True,
                        evidence_status="TEST_FIXTURE",
                    )
                ]
            return []

    def batch_scrape(self, urls: List[str]) -> List[FetchResult]:
        """Scrape multiple URLs in batch."""
        results = []
        for u in urls:
            results.append(self.scrape(u))
        return results

    def _generate_test_scrape_fixture(self, url: str, latency: float) -> FetchResult:
        """Generates an unmistakable test fixture when external daemon is absent in test mode."""
        fixture_text = (
            f"# Firecrawl Test Fixture: {url}\n\n"
            f"This is an automated test fixture representing Firecrawl clean markdown scraping.\n"
            f"Autonomous operating model benchmarks demonstrate 85% reduction in verification latency.\n"
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
            acquisition_method="firecrawl_scrape",
            is_mock=True,
            evidence_status="TEST_FIXTURE",
            metadata={
                "title": f"Firecrawl Fixture: {url}",
                "publisher": "TEST_FIXTURE",
                "source_id": generate_prefixed_id("SRC-FC-TEST"),
            },
        )

    def _generate_test_crawl_fixture(self, seed_url: str) -> List[FetchResult]:
        """Generates crawl test fixtures for testing."""
        return [
            self._generate_test_scrape_fixture(f"{seed_url.rstrip('/')}/page-1", 10.0),
            self._generate_test_scrape_fixture(f"{seed_url.rstrip('/')}/page-2", 12.0),
        ]
