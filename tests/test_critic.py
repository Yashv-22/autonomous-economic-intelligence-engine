"""
Unit Tests for Adversarial Critic & Grounding Evaluation.
"""

import unittest
from src.models.schemas import (
    SourceSpan,
    ExtractedClaim,
    SynthesisResult,
    ProblemHypothesis,
    EvidenceGrade,
)
from src.validation.critic import AdversarialCritic


class TestAdversarialCritic(unittest.TestCase):

    def setUp(self):
        self.critic = AdversarialCritic(strictness_threshold=0.70)
        self.span = SourceSpan(
            document_name="doc.pdf",
            document_hash="1111" * 16,
            page_or_section="Page 1",
            paragraph_index=0,
            text="McKinsey reports 88% adoption.",
            span_hash="aaaa" * 16,
        )
        self.claim1 = ExtractedClaim(
            claim_id="CLAIM-0001",
            text="McKinsey reports 88% adoption.",
            entity_or_topic="Adoption",
            evidence_grade=EvidenceGrade.EVIDENCE,
            source_span=self.span,
            confidence_score=0.95,
        )
        self.assumption_claim = ExtractedClaim(
            claim_id="CLAIM-0002",
            text="Financial model assumes 85% routing rate.",
            entity_or_topic="Routing",
            evidence_grade=EvidenceGrade.ASSUMPTION,
            is_model_assumption=True,
            source_span=self.span,
            confidence_score=0.90,
        )

    def test_audit_synthesis_passes_with_grounded_claims(self):
        """Verify well-grounded synthesis passes adversarial review."""
        synthesis = SynthesisResult(
            synthesis_id="SYN-001",
            objective_id="OBJ-001",
            title="Valid Synthesis",
            summary="88% adoption is observed in enterprises.",
            detailed_findings=["Finding 1"],
            supporting_claim_ids=["CLAIM-0001"],
            cited_span_hashes=[self.span.span_hash],
            contradictions_noted=["CONTRA-0001"],
            epistemic_confidence=0.95,
        )

        passed, notes, revised_conf = self.critic.audit_synthesis_grounding(
            synthesis, [self.claim1]
        )
        self.assertTrue(passed)
        self.assertGreaterEqual(revised_conf, 0.70)

    def test_audit_synthesis_penalizes_unregistered_claims(self):
        """Verify critic penalizes citations not present in the registered claims corpus."""
        synthesis = SynthesisResult(
            synthesis_id="SYN-002",
            objective_id="OBJ-001",
            title="Fabricated Synthesis",
            summary="Fabricated claim not present in corpus.",
            supporting_claim_ids=["CLAIM-9999"],
            epistemic_confidence=0.95,
        )

        passed, notes, revised_conf = self.critic.audit_synthesis_grounding(
            synthesis, [self.claim1]
        )
        self.assertFalse(passed)
        self.assertTrue(any("not registered in claims corpus" in n for n in notes))

    def test_challenge_hypothesis(self):
        """Verify red-teaming checks null hypothesis structure and falsification test clarity."""
        hypo = ProblemHypothesis(
            hypothesis_id="HYPO-0001",
            title="Test Hypothesis",
            statement="Statement of the problem.",
            null_hypothesis="H0: There is no effect.",
            supporting_claim_ids=["CLAIM-0001"],
            opposing_claim_ids=[],
            affected_functions=["Finance"],
            falsification_criteria="Empirical multi-variate regression across 50 audited enterprise value streams.",
        )

        review = self.critic.challenge_hypothesis(hypo, [self.claim1])
        self.assertEqual(review["recommendation"], "APPROVED")
        self.assertEqual(review["falsification_clarity"], "HIGH")
        self.assertTrue(review["has_null_hypothesis"])


if __name__ == "__main__":
    unittest.main()
