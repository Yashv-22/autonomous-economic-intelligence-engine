"""
Unit Tests for Contradiction Detection and Hypothesis Generation.
"""

import unittest
from src.models.schemas import SourceSpan, ExtractedClaim, EvidenceGrade
from src.validation.contradiction import ContradictionDetector, HypothesisGenerator


class TestContradiction(unittest.TestCase):

    def setUp(self):
        self.span1 = SourceSpan(
            document_name="doc1.pdf",
            document_hash="1111111111111111111111111111111111111111111111111111111111111111",
            page_or_section="Page 1",
            paragraph_index=0,
            text="Stanford HAI reports that organizational adoption of generative AI reached 88% across enterprise sectors.",
            span_hash="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )
        self.span2 = SourceSpan(
            document_name="doc2.pdf",
            document_hash="2222222222222222222222222222222222222222222222222222222222222222",
            page_or_section="Page 2",
            paragraph_index=1,
            text="McKinsey finds that over 80% of enterprises report negligible EBITDA impact from initial deployments.",
            span_hash="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        )

        self.claim1 = ExtractedClaim(
            claim_id="CLAIM-0001",
            text=self.span1.text,
            entity_or_topic="AI Adoption",
            evidence_grade=EvidenceGrade.EVIDENCE,
            institution="Stanford HAI",
            quantitative_metric="88%",
            is_model_assumption=False,
            source_span=self.span1,
            confidence_score=0.95,
            tags=["adoption"],
        )
        self.claim2 = ExtractedClaim(
            claim_id="CLAIM-0002",
            text=self.span2.text,
            entity_or_topic="Economic Returns",
            evidence_grade=EvidenceGrade.EVIDENCE,
            institution="McKinsey",
            quantitative_metric="80%",
            is_model_assumption=False,
            source_span=self.span2,
            confidence_score=0.92,
            tags=["ebitda", "paradox"],
        )

    def test_contradiction_detection_distinct_claims(self):
        detector = ContradictionDetector()
        contradictions = detector.detect_contradictions([self.claim1, self.claim2])

        self.assertGreaterEqual(len(contradictions), 1)
        contra = contradictions[0]
        self.assertIn("Paradox", contra.topic)
        self.assertEqual(contra.claim_a.claim_id, "CLAIM-0001")
        self.assertEqual(contra.claim_b.claim_id, "CLAIM-0002")
        self.assertNotEqual(contra.claim_a.claim_id, contra.claim_b.claim_id)
        self.assertNotEqual(contra.claim_a.text, contra.claim_b.text)

    def test_self_matching_prevention(self):
        """Verify that a claim is NEVER matched against itself."""
        detector = ContradictionDetector()
        contradictions = detector.detect_contradictions([self.claim1])
        self.assertEqual(len(contradictions), 0)

    def test_hypothesis_generation(self):
        hypotheses = HypothesisGenerator.generate_hypotheses([self.claim1, self.claim2], [])
        self.assertGreaterEqual(len(hypotheses), 3)

        first_hypo = hypotheses[0]
        self.assertIsNotNone(first_hypo.null_hypothesis)
        self.assertTrue(first_hypo.null_hypothesis.startswith("H0:"))
        self.assertIsNotNone(first_hypo.falsification_criteria)


if __name__ == "__main__":
    unittest.main()
