"""
Unit Tests for Opportunity Validation Lab and Experiment Designer.
Verifies the 5-dimension stress test with evidence-judgment separation,
adversarial Kill Thesis synthesis, and minimum viable experiment design with cost baselines.
"""

import unittest
from src.models.schemas import ExtractedClaim, EvidenceGrade, SourceSpan
from src.opportunity.schemas import SaaSSolutionOpportunity, ValidationVerdict
from src.validation.lab import OpportunityValidationLab
from src.validation.experiment_designer import ExperimentDesigner


class TestOpportunityValidationLab(unittest.TestCase):
    """Test suite for OpportunityValidationLab and ExperimentDesigner."""

    def setUp(self):
        self.opp = SaaSSolutionOpportunity(
            opportunity_id="OPP-001",
            solution_title="DualFlow: Straight-Through Accounting Reconciliation",
            category="B2B SaaS",
            problem_addressed_id="PROB-001",
            problem_title="Dual Execution Latency & Manual Review Backlog",
            target_buyer_icp="Chief Financial Officer / VP of FinOps",
            core_value_proposition="Autonomous cross-ledger straight-through reconciliation engine.",
            what_you_can_offer="Turnkey reconciliation software with cryptographic verification.",
            technical_blueprint="Python FastAPI + Postgres + Merkle Hash Ledger",
            monetization_model="$35,000 / year enterprise subscription",
            estimated_build_time="3 to 4 weeks MVP",
            opportunity_score=8.7,
            roi_multiple="6.5x ROI"
        )
        span = SourceSpan(
            document_name="erp_audit.pdf",
            document_hash="hash001",
            page_or_section="P1",
            paragraph_index=0,
            text="Enterprise ERP reconciliations suffer 48hr delay.",
            span_hash="span001"
        )
        self.claims = [
            ExtractedClaim(
                claim_id="CLM-001",
                text="Enterprise ERP reconciliations suffer 48hr delay.",
                evidence_grade=EvidenceGrade.FACT,
                confidence=0.90,
                source_citation="ERP Field Audit",
                entity_or_topic="Dual Ledger Accounting",
                source_span=span
            )
        ]

    def test_validation_lab_dimensions_structure(self):
        """Verify that all 5 dimensions separate evidence, inference, unknowns, and assessment."""
        report = OpportunityValidationLab.run_validation_lab(self.opp, self.claims, "Dual Ledger Accounting")
        self.assertIsNotNone(report)
        self.assertEqual(report.opportunity_id, "OPP-001")
        self.assertIn("DEMAND", report.dimensions)
        self.assertIn("WILLINGNESS_TO_PAY", report.dimensions)
        self.assertIn("COMPETITION", report.dimensions)
        self.assertIn("FEASIBILITY", report.dimensions)
        self.assertIn("DEFENSIBILITY", report.dimensions)

        for dim_name, dim in report.dimensions.items():
            self.assertGreater(len(dim.evidence_claims), 0)
            self.assertIsNotNone(dim.inference)
            self.assertGreater(len(dim.unknowns), 0)
            self.assertTrue(0.0 <= dim.assessment_score <= 100.0)
            self.assertIn(dim.confidence, ["HIGH", "MEDIUM", "LOW", "UNKNOWN"])
            self.assertIn("Supported by", dim.grounding_summary)

    def test_kill_thesis_and_verdict(self):
        """Verify adversarial Kill Thesis contains critical vulnerabilities and falsification boundaries."""
        report = OpportunityValidationLab.run_validation_lab(self.opp, self.claims, "Dual Ledger Accounting")
        self.assertIsNotNone(report.kill_thesis)
        self.assertIn(report.verdict, [ValidationVerdict.PROCEED_TO_MVP, ValidationVerdict.PILOT_EXPERIMENT_REQUIRED, ValidationVerdict.KILL_OPPORTUNITY_NOW])
        self.assertIsNotNone(report.kill_thesis.critical_vulnerability)
        self.assertIsNotNone(report.kill_thesis.incumbent_crush_risk)
        self.assertIsNotNone(report.kill_thesis.churn_and_retention_risk)
        self.assertGreaterEqual(len(report.kill_thesis.falsification_boundaries), 2)

    def test_experiment_designer_ranked_experiments(self):
        """Verify that ExperimentDesigner yields 4 ranked experiments with cost ranges, basis, and kill criteria."""
        experiments = ExperimentDesigner.design_experiments(
            opportunity_id=self.opp.opportunity_id,
            opportunity_title=self.opp.solution_title,
            target_buyer_icp=self.opp.target_buyer_icp,
            core_value_proposition=self.opp.core_value_proposition,
            problem_description=self.opp.problem_title
        )
        self.assertEqual(len(experiments), 4)

        tiers = [e.tier for e in experiments]
        self.assertIn("LEVEL_1_DISCOVERY", tiers)
        self.assertIn("LEVEL_2_COMMITMENT", tiers)
        self.assertIn("LEVEL_3_CONCIERGE", tiers)
        self.assertIn("LEVEL_4_SYNTHETIC", tiers)

        for exp in experiments:
            self.assertTrue(exp.estimated_cost.startswith("$"))
            self.assertIsNotNone(exp.cost_basis)
            self.assertIn(exp.cost_confidence, ["HIGH", "MEDIUM", "LOW", "UNKNOWN"])
            self.assertIsNotNone(exp.estimated_time)
            self.assertTrue(0.0 <= exp.expected_information_gain <= 1.0)
            self.assertIsNotNone(exp.success_criterion)
            self.assertIsNotNone(exp.kill_criterion)


if __name__ == "__main__":
    unittest.main()
