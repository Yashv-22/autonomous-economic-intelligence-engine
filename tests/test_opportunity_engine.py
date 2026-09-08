"""
Unit Tests for Opportunity Discovery & Economic Intelligence Engine.
Verifies inspectable heuristic scoring, hard epistemic evidence boundary enforcement,
solution blueprints, and adversarial validation reports.
"""

import unittest
from src.opportunity.engine import OpportunityDiscoveryEngine
from src.opportunity.schemas import (
    EpistemicCertainty,
    ValidationVerdict,
    OpportunityMatrixResponse,
)


class TestOpportunityDiscoveryEngine(unittest.TestCase):

    def setUp(self):
        self.engine = OpportunityDiscoveryEngine()

    def test_opportunity_index_formula(self):
        """Verify heuristic opportunity index formula produces bounded, reproducible scores."""
        score = self.engine.calculate_opportunity_index(
            economic_score=9.0,
            urgency_score=9.0,
            wtp_score=8.5,
            automation_potential=0.85,
            market_score=9.0,
            feasibility_factor=0.90,
            moat_factor=0.85,
            impl_complexity=3.5,
            governance_risk=2.0,
        )
        self.assertGreaterEqual(score, 7.0)
        self.assertLessEqual(score, 10.0)

    def test_discover_opportunities_structure(self):
        matrix: OpportunityMatrixResponse = self.engine.discover_opportunities()
        self.assertGreaterEqual(matrix.total_problems_identified, 3)
        self.assertGreaterEqual(matrix.total_solutions_generated, 3)
        self.assertEqual(len(matrix.market_problems), matrix.total_problems_identified)
        self.assertEqual(len(matrix.solution_opportunities), matrix.total_solutions_generated)

    def test_hard_epistemic_evidence_boundary(self):
        """Verify that problems strictly categorize evidence into FACT, INFERENCE, HYPOTHESIS, ESTIMATE, UNKNOWN."""
        matrix = self.engine.discover_opportunities()
        prob1 = matrix.market_problems[0]
        self.assertGreaterEqual(len(prob1.epistemic_evidence), 3)

        categories = {item.category for item in prob1.epistemic_evidence}
        self.assertIn(EpistemicCertainty.FACT, categories)
        self.assertIn(EpistemicCertainty.INFERENCE, categories)

        # Verify that FACT items have source citations
        for item in prob1.epistemic_evidence:
            if item.category == EpistemicCertainty.FACT:
                self.assertIsNotNone(item.source_citation)

    def test_inspectable_dimensions_and_ranking_rationale(self):
        """Verify that opportunity ranking provides qualitative inspectability ('Why Ranked #1')."""
        matrix = self.engine.discover_opportunities()
        opp1 = matrix.solution_opportunities[0]

        self.assertIsNotNone(opp1.score_breakdown)
        self.assertEqual(opp1.score_breakdown.label, "heuristic ranking")
        self.assertTrue(len(opp1.score_breakdown.ranking_rationale) > 20)

        dims = opp1.score_breakdown.dimensions
        self.assertIn(dims.demand_evidence, ["Strong", "Moderate", "Weak"])
        self.assertIn(dims.problem_severity, ["Critical", "High", "Moderate", "Low"])
        self.assertIn(dims.wtp_evidence, ["Strong", "Moderate", "Speculative"])
        self.assertIsInstance(dims.unknowns, list)

    def test_adversarial_validation_report(self):
        """Verify adversarial validation includes pro/contra evidence and valid verdict."""
        matrix = self.engine.discover_opportunities()
        for opp in matrix.solution_opportunities:
            report = opp.validation_report
            self.assertIsNotNone(report)
            self.assertGreaterEqual(len(report.pro_demand_evidence), 1)
            self.assertGreaterEqual(len(report.critical_assumptions), 1)
            self.assertGreaterEqual(len(report.existing_competitors), 1)
            self.assertIn(report.verdict, [
                ValidationVerdict.PROCEED_TO_MVP,
                ValidationVerdict.PILOT_EXPERIMENT_REQUIRED,
                ValidationVerdict.DO_NOT_BUILD_YET,
            ])
            self.assertIn("cheapest_validation_experiment", report.__dict__)

    def test_solution_blueprint_completeness(self):
        """Verify that each opportunity includes a complete architectural blueprint."""
        matrix = self.engine.discover_opportunities()
        for opp in matrix.solution_opportunities:
            bp = opp.blueprint
            self.assertIsNotNone(bp)
            self.assertTrue(bp.concept)
            self.assertTrue(bp.target_buyer_icp)
            self.assertTrue(bp.mvp_specification)
            self.assertTrue(bp.technical_architecture)
            self.assertGreaterEqual(len(bp.integrations), 1)

    def test_get_by_id_helpers(self):
        opp = self.engine.get_opportunity_by_id("OPP-001")
        self.assertIsNotNone(opp)
        self.assertEqual(opp.opportunity_id, "OPP-001")

        report = self.engine.get_validation_report("OPP-001")
        self.assertIsNotNone(report)
        self.assertEqual(report.opportunity_id, "OPP-001")

        blueprint = self.engine.get_solution_blueprint("OPP-001")
        self.assertIsNotNone(blueprint)
        self.assertIn("straight-through", blueprint.concept.lower())

    def test_dynamic_topic_multi_opportunity_and_offerings(self):
        """Verify custom research topics yield at least 8 distinct opportunities, problems, and what_you_can_offer deliverables."""
        matrix = self.engine.discover_opportunities(claims=[], topic="What are the problems in Dual Ledger Accounting")
        self.assertGreaterEqual(matrix.total_problems_identified, 8)
        self.assertGreaterEqual(matrix.total_solutions_generated, 8)
        self.assertEqual(len(matrix.market_problems), 8)
        self.assertEqual(len(matrix.solution_opportunities), 8)

        for opp in matrix.solution_opportunities:
            self.assertTrue(bool(opp.what_you_can_offer))
            self.assertTrue(bool(opp.problem_title))
            self.assertTrue(bool(opp.core_value_proposition))
            self.assertTrue(bool(opp.target_buyer_icp))
            self.assertGreater(len(opp.what_you_can_offer), 20)

        for prob in matrix.market_problems:
            self.assertTrue(bool(prob.title))
            self.assertTrue(bool(prob.description))
            self.assertTrue(bool(prob.root_cause))

    def test_ai_operating_model_domain_yields_8_opportunities(self):
        """Verify standard AI operating model domain benchmark yields 8 opportunities and problems."""
        matrix = self.engine.discover_opportunities(claims=[], topic="Enterprise AI Operating Model Redesign")
        self.assertGreaterEqual(matrix.total_problems_identified, 8)
        self.assertGreaterEqual(matrix.total_solutions_generated, 8)
        self.assertEqual(len(matrix.market_problems), 8)
        self.assertEqual(len(matrix.solution_opportunities), 8)


if __name__ == "__main__":
    unittest.main()

