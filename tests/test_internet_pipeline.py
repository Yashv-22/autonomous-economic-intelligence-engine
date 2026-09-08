"""
Unit Tests for Internet Intelligence & Acquisition Pipeline.
Validates Discovery, Acquisition, Normalization, Provenance, and the unified Pipeline.
"""

import unittest
from unittest.mock import patch, MagicMock

from src.internet.providers.base import SearchResultItem, FetchResult
from src.internet.discovery.engine import DiscoveryEngine
from src.internet.acquisition.engine import AcquisitionEngine
from src.internet.normalization.engine import NormalizationEngine
from src.internet.provenance.tracker import InternetProvenanceTracker
from src.internet.pipeline import InternetAcquisitionPipeline
from src.core.identifiers import compute_sha256


class TestInternetAcquisitionPipeline(unittest.TestCase):

    def test_discovery_engine(self):
        mock_agent_reach = MagicMock()
        mock_agent_reach.search.return_value = [
            SearchResultItem(
                url="https://example.com/research1",
                title="AI Transformation Report",
                snippet="84% of organizations have not redesigned their operating model.",
                source_domain="example.com",
                provider="agent_reach",
            )
        ]
        mock_fallback_search = MagicMock()
        mock_fallback_search.search.return_value = []

        engine = DiscoveryEngine(
            search_engine=mock_fallback_search,
            agent_reach_search=mock_agent_reach,
        )
        results = engine.discover_sources(["enterprise AI bottlenecks"], budget_per_query=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, "https://example.com/research1")

    def test_acquisition_engine_ssrf_and_sanitization(self):
        clean_bytes = b"Enterprise AI straight-through routing reduces queue drift by 70%."
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = FetchResult(
            url="https://example.com/clean",
            final_url="https://example.com/clean",
            status_code=200,
            content_type="text/plain",
            raw_content=clean_bytes,
            content_hash=compute_sha256(clean_bytes),
        )

        acq = AcquisitionEngine(fetcher=mock_fetcher)
        items = [
            SearchResultItem(
                url="https://example.com/clean",
                title="Clean Source",
                snippet="...",
                source_domain="example.com",
                provider="agent_reach",
            ),
            SearchResultItem(
                url="http://169.254.169.254/latest/meta-data",
                title="Cloud Metadata",
                snippet="...",
                source_domain="169.254.169.254",
                provider="agent_reach",
            ),
        ]

        results = acq.acquire_sources(items)
        # SSRF should block 169.254.169.254 and only acquire the clean URL
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, "https://example.com/clean")

    def test_normalization_and_provenance(self):
        norm = NormalizationEngine()
        raw_text = "First paragraph with critical market data on AI ROI.\n\nSecond paragraph explaining handoff queues and operational friction."
        raw_b = raw_text.encode("utf-8")
        fetched = [
            FetchResult(
                url="https://example.com/doc1",
                final_url="https://example.com/doc1",
                status_code=200,
                content_type="text/plain",
                raw_content=raw_b,
                content_hash=compute_sha256(raw_b),
            )
        ]
        docs = norm.normalize(fetched)
        self.assertEqual(len(docs), 1)
        self.assertEqual(len(docs[0].chunks), 2)

        tracker = InternetProvenanceTracker()
        spans = tracker.track_and_register(docs)
        self.assertEqual(len(spans), 2)
        self.assertTrue(spans[0].span_hash)
        self.assertEqual(spans[0].document_name, "https://example.com/doc1")
        self.assertIsNotNone(tracker.ledger.compute_merkle_root())

    def test_full_pipeline_orchestration(self):
        mock_agent_reach = MagicMock()
        mock_agent_reach.search.return_value = [
            SearchResultItem(
                url="https://example.com/ai-ops",
                title="AI Ops Study",
                snippet="Evidence of enterprise AI adoption vs EBITDA return divergence.",
                source_domain="example.com",
                provider="agent_reach",
            )
        ]
        mock_fallback = MagicMock()
        mock_fallback.search.return_value = []

        test_content = b"McKinsey survey reveals that 72% of companies deploying AI see no EBITDA impact without workflow redesign."
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = FetchResult(
            url="https://example.com/ai-ops",
            final_url="https://example.com/ai-ops",
            status_code=200,
            content_type="text/plain",
            raw_content=test_content,
            content_hash=compute_sha256(test_content),
        )

        pipeline = InternetAcquisitionPipeline(
            discovery=DiscoveryEngine(
                search_engine=mock_fallback,
                agent_reach_search=mock_agent_reach,
            ),
            acquisition=AcquisitionEngine(fetcher=mock_fetcher),
            normalization=NormalizationEngine(),
            provenance_tracker=InternetProvenanceTracker(),
        )

        spans = pipeline.execute(["AI operating model EBITDA ROI"], max_sources=1)
        self.assertGreaterEqual(len(spans), 1)
        self.assertIn("McKinsey", spans[0].text)
        self.assertTrue(spans[0].span_hash)


if __name__ == "__main__":
    unittest.main()
