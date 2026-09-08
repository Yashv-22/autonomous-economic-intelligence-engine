"""
Internet Acquisition Module.
Fetches remote web and platform content using Agent Reach and WebFetcher,
enforcing SSRF prevention, timeouts, rate-limiting, and prompt injection isolation.
"""

from typing import List, Dict, Any, Optional
from src.internet.providers.base import FetchResult, SearchResultItem
from src.internet.providers.agent_reach_provider import AgentReachFetchProvider
from src.internet.fetcher.fetcher import WebFetcher
from src.security.network import network_validator
from src.security.sanitizer import ContentSanitizer
from src.core.logging import logger


class AcquisitionEngine:
    """
    Secure internet content acquisition engine.
    """

    def __init__(self, fetcher: Optional[WebFetcher] = None):
        self.fetcher = fetcher or WebFetcher()
        self.agent_reach_fetcher = AgentReachFetchProvider()

    def acquire_sources(
        self,
        sources: List[SearchResultItem],
        max_sources: int = 10,
    ) -> List[FetchResult]:
        """
        Acquire full text content for discovered search items.
        Applies SSRF validation and isolates untrusted external data.
        """
        acquired: List[FetchResult] = []

        for item in sources[:max_sources]:
            url = item.url
            if not url:
                continue

            # 1. SSRF and scheme validation
            try:
                network_validator.validate_url(url)
            except Exception as e:
                logger.warning(f"Acquisition blocked by security policy for '{url}': {e}")
                continue

            # 2. Acquire content via Agent Reach fetcher first, then WebFetcher
            result: Optional[FetchResult] = None
            try:
                res = self.agent_reach_fetcher.fetch(url)
                if res and res.status_code == 200 and res.content:
                    result = res
            except Exception as e:
                logger.debug(f"Agent Reach fetch fallback triggered for '{url}': {e}")

            if not result or not result.raw_content:
                try:
                    result = self.fetcher.fetch(url)
                except Exception as e:
                    logger.warning(f"WebFetcher failed for '{url}': {e}")
                    continue

            if result and result.raw_content:
                # 3. Prompt injection detection and sanitization
                text = result.raw_content.decode("utf-8", errors="replace")
                is_inj, cleaned_text = ContentSanitizer.detect_prompt_injection(text)
                if is_inj:
                    logger.warning(f"Prompt injection risk detected in source '{url}'. Content sanitized.")
                    result.raw_content = ContentSanitizer.sanitize_untrusted_text(text).encode("utf-8")
                acquired.append(result)

        logger.info(f"AcquisitionEngine: Successfully acquired {len(acquired)}/{len(sources)} sources.")
        return acquired
