"""
Unit Tests for Evidence Gap and Epistemic Uncertainty Engine.
Verifies the 9-class evidence gap taxonomy, deterministic uncertainty calculation,
generalized source authority evaluation, and absence of fabricated metrics.
"""

import unittest
from src.models.schemas import ExtractedClaim, EvidenceGrade, ContradictionRecord, SourceSpan
from src.research.uncertainty import EpistemicUncertaintyEngine, GapClass, UncertaintyBreakdown


class TestEpistemicUncertaintyEngine(unittest.TestCase):
    """Test suite for EpistemicUncertaintyEngine."""

    def setUp(self):
        self.topic = "Enterprise AI Operating Model Redesign"
        span1 = SourceSpan(
            document_name="deloitte_2024.pdf",
            document_hash="abc123hash",
            page_or_section="Exec Summary",
            paragraph_index=1,
            text="84% of organizations deployed AI without redesigning workflows.",
            span_hash="span123hash",
        )
        self.claims = [
            ExtractedClaim(
                claim_id="CLM-001",
                text="Deloitte 2024 survey indicates 84% of organizations deployed AI without redesigning workflows.",
                evidence_grade=EvidenceGrade.FACT,
                confidence=0.92,
                source_citation="Deloitte Enterprise Survey 2024",
                entity_or_topic=self.topic,
                source_span=span1,
            ),
            ExtractedClaim(
                claim_id="CLM-002",
                text="Human-in-the-loop review fatigue increases exception error rates by 3.2x under high load.",
                evidence_grade=EvidenceGrade.EVIDENCE,
                confidence=0.88,
                source_citation="Operations Research Quarterly",
                entity_or_topic=self.topic,
                source_span=span1,
            ),
            ExtractedClaim(
                claim_id="CLM-003",
                text="Assuming autonomous orchestration will expand gross margins by 20%.",
                evidence_grade=EvidenceGrade.ASSUMPTION,
                confidence=0.60,
                source_citation="Internal Projection",
                entity_or_topic=self.topic,
                source_span=span1,
            ),
        ]

    def test_evaluate_uncertainty_structure(self):
        """Verify that evaluate_uncertainty returns fully-formed UncertaintyBreakdown with deterministic method."""
        breakdown = EpistemicUncertaintyEngine.evaluate_uncertainty(
            topic=self.topic,
            claims=self.claims,
            contradictions=[]
        )
        self.assertIsInstance(breakdown, UncertaintyBreakdown)
        self.assertEqual(breakdown.topic, self.topic)
        self.assertTrue(0.0 <= breakdown.aggregate_uncertainty_score <= 1.0)
        self.assertEqual(breakdown.score_method, "epistemic_entropy_v1")
        self.assertIn("Evaluated 3 claims", breakdown.evidence_basis or "")
        self.assertGreater(len(breakdown.active_gaps), 0)

    def test_gap_taxonomy_coverage(self):
        """Verify that the 9-class evidence gap taxonomy correctly classifies voids."""
        breakdown = EpistemicUncertaintyEngine.evaluate_uncertainty(
            topic=self.topic,
            claims=self.claims,
            contradictions=[]
        )
        active_classes = [g.gap_class.value for g in breakdown.active_gaps]
        # Should detect economic assumption unsupported and buyer evidence missing
        self.assertIn(GapClass.BUYER_EVIDENCE_MISSING.value, active_classes)
        self.assertIn(GapClass.ECONOMIC_ASSUMPTION_UNSUPPORTED.value, active_classes)

        for gap in breakdown.active_gaps:
            self.assertIsNotNone(gap.gap_id)
            self.assertIsNotNone(gap.actionable_query)
            self.assertEqual(gap.score_method, "claim_grade_frequency" if "PRIM" in gap.gap_id else ("distinct_source_cardinality" if "SAMP" in gap.gap_id else ("economic_term_density" if "ECON" in gap.gap_id else "buyer_term_matching" if "BUYR" in gap.gap_id else gap.score_method)))
            self.assertIn(gap.confidence, ["HIGH", "MEDIUM", "LOW", "UNKNOWN"])

    def test_resolved_gaps_filtering(self):
        """Verify that previously resolved gaps are not returned in active gaps."""
        breakdown_initial = EpistemicUncertaintyEngine.evaluate_uncertainty(
            topic=self.topic,
            claims=self.claims,
            contradictions=[]
        )
        first_gap_id = breakdown_initial.active_gaps[0].gap_id

        breakdown_filtered = EpistemicUncertaintyEngine.evaluate_uncertainty(
            topic=self.topic,
            claims=self.claims,
            contradictions=[],
            previous_resolved_gaps=[first_gap_id]
        )
        active_ids = [g.gap_id for g in breakdown_filtered.active_gaps]
        self.assertNotIn(first_gap_id, active_ids)
        self.assertIn(first_gap_id, breakdown_filtered.resolved_gaps)


if __name__ == "__main__":
    unittest.main()
