"""
Internet Layer Package.
Provides search providers, crawler, fetcher, parsers, and ranking.
"""

from src.internet.providers.base import (
    BaseSearchProvider,
    BaseFetchProvider,
    SearchResultItem,
    FetchResult,
)
from src.internet.search.engine import MultiProviderSearchEngine
from src.internet.fetcher.fetcher import WebFetcher
from src.internet.crawler.crawler import AutonomousWebCrawler, CrawledPage
from src.internet.parsers.web_parser import WebContentParser
from src.internet.ranking.source_ranker import SourceRanker

from src.internet.discovery.engine import DiscoveryEngine
from src.internet.acquisition.engine import AcquisitionEngine
from src.internet.normalization.engine import NormalizationEngine, NormalizedSourceDocument
from src.internet.provenance.tracker import InternetProvenanceTracker
from src.internet.pipeline import InternetAcquisitionPipeline

__all__ = [
    "BaseSearchProvider",
    "BaseFetchProvider",
    "SearchResultItem",
    "FetchResult",
    "MultiProviderSearchEngine",
    "WebFetcher",
    "AutonomousWebCrawler",
    "CrawledPage",
    "WebContentParser",
    "SourceRanker",
    "DiscoveryEngine",
    "AcquisitionEngine",
    "NormalizationEngine",
    "NormalizedSourceDocument",
    "InternetProvenanceTracker",
    "InternetAcquisitionPipeline",
]
