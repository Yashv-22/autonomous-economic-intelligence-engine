"""
Internet Discovery Module.
Discovers relevant sources across Agent Reach channels (Exa, GitHub, RSS, YouTube) and search engines.
"""

from typing import List, Dict, Any, Optional
from src.internet.providers.base import SearchResultItem
from src.internet.providers.agent_reach_provider import AgentReachSearchProvider
from src.internet.search.engine import MultiProviderSearchEngine
from src.core.logging import logger


class DiscoveryEngine:
    """
    Multi-channel internet discovery engine with Agent Reach integration.
    """

    def __init__(
        self,
        search_engine: Optional[MultiProviderSearchEngine] = None,
        agent_reach_search: Optional[AgentReachSearchProvider] = None,
    ):
        self.search_engine = search_engine or MultiProviderSearchEngine()
        self.agent_reach = agent_reach_search or AgentReachSearchProvider()

    def discover_sources(
        self,
        queries: List[str],
        budget_per_query: int = 5,
        channel: Optional[str] = None,
    ) -> List[SearchResultItem]:
        """
        Execute multi-channel source discovery for research queries.
        Prioritizes Agent Reach channels with resilient multi-provider fallback.
        """
        all_results: List[SearchResultItem] = []
        seen_urls = set()

        for query in queries:
            logger.info(f"DiscoveryEngine: Probing sources for query: '{query}'")
            items = []

            # 1. Attempt Agent Reach multi-channel discovery
            try:
                agent_reach_results = self.agent_reach.search(query, max_results=budget_per_query, channel=channel)
                if agent_reach_results:
                    items.extend(agent_reach_results)
            except Exception as e:
                logger.warning(f"Agent Reach discovery skipped for '{query}': {e}")

            # 2. Fall back to multi-provider search engine if fewer than desired results
            if len(items) < budget_per_query:
                try:
                    fallback_results = self.search_engine.search(query, max_results=budget_per_query - len(items))
                    items.extend(fallback_results)
                except Exception as e:
                    logger.warning(f"Multi-provider search fallback failed for '{query}': {e}")

            # Deduplicate by URL
            for item in items:
                if item.url and item.url not in seen_urls:
                    seen_urls.add(item.url)
                    all_results.append(item)

        logger.info(f"DiscoveryEngine: Discovered {len(all_results)} unique sources across {len(queries)} queries.")
        return all_results
