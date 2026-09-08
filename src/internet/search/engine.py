"""
Multi-Provider Search Engine.
Orchestrates multi-dimensional queries across primary, secondary, academic, and industry providers with automatic failover.
"""

from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from src.internet.providers.base import BaseSearchProvider, SearchResultItem
from src.internet.providers.duckduckgo import DuckDuckGoSearchProvider
from src.internet.providers.arxiv import ArXivSearchProvider
from src.internet.providers.wikipedia import WikipediaSearchProvider
from src.internet.providers.mock_provider import MockSearchProvider
from src.internet.providers.agent_reach_provider import AgentReachSearchProvider
from src.core.logging import logger


import os
import concurrent.futures

class MultiProviderSearchEngine:
    """Enterprise-grade search engine with dynamic provider failover and result merging."""

    def __init__(
        self,
        primary_provider: Optional[BaseSearchProvider] = None,
        secondary_providers: Optional[List[BaseSearchProvider]] = None,
        providers: Optional[List[BaseSearchProvider]] = None,
        fallback_to_mock: bool = True,
        enable_agent_reach: bool = True,
    ):
        if providers:
            self.primary_provider = providers[0]
            self.secondary_providers = providers[1:] if len(providers) > 1 else []
        else:
            default_secondary: List[BaseSearchProvider] = []
            agent_reach = AgentReachSearchProvider() if enable_agent_reach else None
            
            # Prefer AgentReach with Exa as primary if configured, which is sub-second
            if agent_reach and os.environ.get("EXA_API_KEY"):
                self.primary_provider = primary_provider or agent_reach
            else:
                self.primary_provider = primary_provider or DuckDuckGoSearchProvider()
                if agent_reach:
                    default_secondary.append(agent_reach)

            default_secondary.extend([
                ArXivSearchProvider(),
                WikipediaSearchProvider(),
            ])
            self.secondary_providers = secondary_providers if secondary_providers is not None else default_secondary
        self.mock_provider = MockSearchProvider()
        self.fallback_to_mock = fallback_to_mock

    def search(
        self,
        query: str,
        max_results: int = 15,
        dimension: Optional[str] = None,
        include_academic: bool = True,
    ) -> List[SearchResultItem]:
        """
        Execute multi-provider search across web and academic providers, deduplicating and merging results.
        """
        all_results: List[SearchResultItem] = []
        seen_urls = set()

        # 1. Primary web search
        try:
            primary_res = self.primary_provider.search(query, max_results=max_results)
            for r in primary_res:
                norm_url = r.url.rstrip("/").lower()
                if norm_url not in seen_urls:
                    seen_urls.add(norm_url)
                    all_results.append(r)
        except Exception as e:
            logger.warning(f"Primary search provider '{self.primary_provider.provider_name}' error: {e}")

        # If primary returned 0 results and primary was not DuckDuckGo, try DDG fallback
        if not all_results and getattr(self.primary_provider, "provider_name", "") != "duckduckgo":
            try:
                ddg = DuckDuckGoSearchProvider()
                ddg_res = ddg.search(query, max_results=max_results)
                for r in ddg_res:
                    norm_url = r.url.rstrip("/").lower()
                    if norm_url not in seen_urls:
                        seen_urls.add(norm_url)
                        all_results.append(r)
            except Exception as ddg_err:
                logger.debug(f"Fallback DDG error: {ddg_err}")

        # 2. Academic / Domain specific search executed in parallel
        if (include_academic or (dimension and dimension.lower() in ["academic", "technical", "economic"])) and self.secondary_providers:
            def _run_sec_search(prov):
                try:
                    return prov.search(query, max_results=5)
                except Exception as err:
                    logger.warning(f"Secondary search provider '{prov.provider_name}' error: {err}")
                    return []

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(self.secondary_providers), 4)) as executor:
                for sec_res in executor.map(_run_sec_search, self.secondary_providers):
                    for r in sec_res:
                        norm_url = r.url.rstrip("/").lower()
                        if norm_url not in seen_urls:
                            seen_urls.add(norm_url)
                            all_results.append(r)

        # 3. Fallback to mock provider if offline / no results found
        if not all_results and self.fallback_to_mock:
            logger.info("Live providers yielded zero results. Falling back to MockSearchProvider.")
            mock_res = self.mock_provider.search(query, max_results=max_results)
            for r in mock_res:
                norm_url = r.url.rstrip("/").lower()
                if norm_url not in seen_urls:
                    seen_urls.add(norm_url)
                    all_results.append(r)

        # Sort by relevance and rank
        all_results.sort(key=lambda x: (x.relevance_score, -x.rank), reverse=True)
        return all_results[:max_results]
