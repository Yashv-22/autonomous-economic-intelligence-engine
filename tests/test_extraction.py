"""
Unit Tests for Claim Extraction and Evidence Grading.
"""

import unittest
from src.models.schemas import SourceSpan, EvidenceGrade
from src.extraction.classifier import EvidenceClassifier
from src.extraction.claim_extractor import ClaimExtractor


class TestExtraction(unittest.TestCase):

    def setUp(self):
        self.dummy_span = SourceSpan(
            document_name="test_report.pdf",
            document_hash="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            page_or_section="Executive Summary",
            paragraph_index=0,
            text="McKinsey reports that 88% of enterprises adopted generative AI tools, but 80% see no material EBITDA uplift.",
            span_hash="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        )

    def test_classifier_heuristics(self):
        # Empirical evidence claim
        grade, is_assump, conf = EvidenceClassifier.classify(
            "PwC survey shows that 74% of economic gains accrue to top 20% of leaders."
        )
        self.assertEqual(grade, EvidenceGrade.EVIDENCE)
        self.assertFalse(is_assump)

        # Model assumption claim
        grade, is_assump, conf = EvidenceClassifier.classify(
            "Parameters model a mid-sized enterprise assuming an 85% straight-through automation rate."
        )
        self.assertEqual(grade, EvidenceGrade.ASSUMPTION)
        self.assertTrue(is_assump)

        # Recommendation claim
        grade, is_assump, conf = EvidenceClassifier.classify(
            "Enterprises must redesign workflows and establish explicit decision rights before buying tools."
        )
        self.assertEqual(grade, EvidenceGrade.RECOMMENDATION)

    def test_claim_extractor(self):
        extractor = ClaimExtractor()
        claims = extractor.extract_claims_from_spans([self.dummy_span])

        self.assertGreaterEqual(len(claims), 1)
        first_claim = claims[0]
        self.assertEqual(first_claim.institution, "McKinsey")
        self.assertIsNotNone(first_claim.quantitative_metric)
        self.assertEqual(first_claim.source_span.document_name, "test_report.pdf")


if __name__ == "__main__":
    unittest.main()
