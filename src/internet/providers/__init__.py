"""
Internet Providers Package.
"""

from src.internet.providers.base import (
    BaseSearchProvider,
    BaseFetchProvider,
    SearchResultItem,
    FetchResult,
)
from src.internet.providers.duckduckgo import DuckDuckGoSearchProvider
from src.internet.providers.arxiv import ArXivSearchProvider
from src.internet.providers.wikipedia import WikipediaSearchProvider
from src.internet.providers.mock_provider import MockSearchProvider, ReplaySearchProvider, MockFetchProvider
from src.internet.providers.agent_reach_provider import AgentReachSearchProvider, AgentReachFetchProvider

__all__ = [
    "BaseSearchProvider",
    "BaseFetchProvider",
    "SearchResultItem",
    "FetchResult",
    "DuckDuckGoSearchProvider",
    "ArXivSearchProvider",
    "WikipediaSearchProvider",
    "MockSearchProvider",
    "ReplaySearchProvider",
    "MockFetchProvider",
    "AgentReachSearchProvider",
    "AgentReachFetchProvider",
]
