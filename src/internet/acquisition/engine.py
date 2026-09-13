"""
Internet Acquisition Module.
Fetches remote web and platform content using Agent Reach and WebFetcher,
enforcing SSRF prevention, timeouts, rate-limiting, and prompt injection isolation.
"""

from typing import List, Dict, Any, Optional
from src.internet.providers.base import FetchResult, SearchResultItem
from src.internet.providers.agent_reach_provider import AgentReachFetchProvider
from src.internet.fetcher.fetcher import WebFetcher
from src.internet.acquisition.router import AdaptiveAcquisitionRouter, AcquisitionRequirement
from src.security.network import network_validator
from src.security.sanitizer import ContentSanitizer
from src.core.logging import logger


class AcquisitionEngine:
    """
    Secure internet content acquisition engine powered by AdaptiveAcquisitionRouter.
    """

    def __init__(
        self,
        fetcher: Optional[WebFetcher] = None,
        router: Optional[AdaptiveAcquisitionRouter] = None,
    ):
        self.fetcher = fetcher or WebFetcher()
        self.agent_reach_fetcher = AgentReachFetchProvider()
        self.router = router or AdaptiveAcquisitionRouter(
            native_fetcher=self.fetcher,
            agent_reach_fetcher=self.agent_reach_fetcher,
        )

    def acquire_sources(
        self,
        sources: List[SearchResultItem],
        max_sources: int = 10,
        needs_javascript: bool = False,
        research_run_id: Optional[str] = None,
    ) -> List[FetchResult]:
        """
        Acquire full text content for discovered search items using adaptive routing.
        Applies SSRF validation, dynamic fallback, and isolates untrusted external data.
        """
        acquired: List[FetchResult] = []

        for item in sources[:max_sources]:
            url = item.url
            if not url:
                continue

            req = AcquisitionRequirement(
                url=url,
                capability="render_dynamic" if needs_javascript else "fetch",
                needs_javascript=needs_javascript,
                research_run_id=research_run_id,
            )

            try:
                result, audit = self.router.route_acquisition(req)
                if result and result.is_success and result.raw_content:
                    acquired.append(result)
            except Exception as e:
                logger.warning(f"AcquisitionEngine: Routing error for '{url}': {e}")
                continue

        logger.info(f"AcquisitionEngine: Successfully acquired {len(acquired)}/{len(sources[:max_sources])} sources.")
        return acquired
