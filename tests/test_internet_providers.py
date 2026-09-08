"""
Unit tests for Internet Search and Fetch Providers.
"""

import unittest
from src.internet.providers.mock_provider import MockSearchProvider, ReplaySearchProvider
from src.internet.providers.arxiv import ArXivSearchProvider
from src.internet.providers.wikipedia import WikipediaSearchProvider
from src.internet.search.engine import MultiProviderSearchEngine
from src.internet.ranking.source_ranker import SourceRanker


class TestInternetProviders(unittest.TestCase):

    def test_mock_search_provider(self):
        prov = MockSearchProvider()
        results = prov.search("enterprise AI operating model McKinsey BCG", max_results=3)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].provider, "mock")
        domains = [r.source_domain.lower() for r in results]
        self.assertTrue(any("mckinsey" in d or "bcg" in d or "deloitte" in d for d in domains))

    def test_source_ranker_academic_priority(self):
        prov = MockSearchProvider()
        results = prov.search("enterprise AI", max_results=10)
        ranked = SourceRanker.rank_sources(results, "enterprise AI operating model")
        self.assertGreater(len(ranked), 0)
        # Verify rank ordering
        self.assertEqual(ranked[0].rank, 1)
        self.assertGreaterEqual(ranked[0].relevance_score, ranked[-1].relevance_score)

    def test_multi_provider_search_engine(self):
        engine = MultiProviderSearchEngine(
            primary_provider=MockSearchProvider(),
            secondary_providers=[],
            fallback_to_mock=True,
        )
        results = engine.search("EBITDA operating model straight through routing", max_results=5)
        self.assertGreaterEqual(len(results), 1)
        urls = [r.url for r in results]
        self.assertEqual(len(urls), len(set(urls)))  # Ensure deduplication


if __name__ == "__main__":
    unittest.main()
