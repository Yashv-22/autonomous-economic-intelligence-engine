"""
Unit tests for Research Memory and Saturation Tracking.
"""

import unittest
import tempfile
import os
from src.research.memory.session_store import ResearchSessionStore
from src.research.saturation.tracker import ResearchSaturationTracker


class TestResearchMemoryAndSaturation(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.session_store = ResearchSessionStore(base_dir=self.temp_dir)

    def test_session_lifecycle_and_persistence(self):
        session = self.session_store.create_or_load_session(topic="Enterprise AI Redesign")
        self.assertIsNotNone(session.session_id)
        
        self.session_store.record_query_execution(session, "AI operating model", 5)
        self.session_store.record_visited_urls(session, ["https://mckinsey.com/ai"])
        
        # Reload from disk
        reloaded = self.session_store.create_or_load_session(topic="Enterprise AI Redesign")
        self.assertEqual(reloaded.session_id, session.session_id)
        self.assertIn("AI operating model", reloaded.executed_queries)
        self.assertIn("https://mckinsey.com/ai", reloaded.visited_urls)

    def test_saturation_tracker_diminishing_returns(self):
        tracker = ResearchSaturationTracker(min_marginal_gain_threshold=0.15)
        
        # High novelty -> Not saturated
        metrics_active = tracker.evaluate_saturation(
            total_sources_seen=5,
            new_sources_acquired=5,
            total_claims_before=10,
            new_claims_extracted=25,
            total_entities_before=2,
            new_entities_found=6,
            open_gaps_count=4,
            resolved_gaps_count=2,
        )
        self.assertFalse(metrics_active.is_saturated)

        # High redundancy / zero new claims -> Saturated
        metrics_saturated = tracker.evaluate_saturation(
            total_sources_seen=25,
            new_sources_acquired=0,
            total_claims_before=200,
            new_claims_extracted=0,
            total_entities_before=50,
            new_entities_found=0,
            open_gaps_count=1,
            resolved_gaps_count=10,
        )
        self.assertTrue(metrics_saturated.is_saturated)
        self.assertIn("RESEARCH SATURATION REACHED", metrics_saturated.saturation_reason)


if __name__ == "__main__":
    unittest.main()
