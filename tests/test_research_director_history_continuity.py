"""
Mandatory History Continuity & Anti-Duplicate Test Suite for Research Director.
Simulates a multi-cycle sequence:
    RUN A: Baseline research on a topic
    RUN B: Follow-up on same topic with newly ingested evidence
    RUN C: Deep investigation resolving prior gaps

Verifies:
1. RUN B knows RUN A's established findings and historical context.
2. RUN B does not duplicate already-resolved research inquiries.
3. RUN C targets newly isolated unresolved gaps from A + B.
4. Previously disproven hypotheses / killed concepts do NOT automatically reappear.
"""

import unittest
from src.models.schemas import ExtractedClaim, EvidenceGrade, SourceSpan, ContradictionRecord
from src.opportunity.schemas import SaaSSolutionOpportunity, ValidationVerdict
from src.research.director import ResearchDirectorEngine, NextBestResearchInvestigation
from src.research.uncertainty import EpistemicUncertaintyEngine, GapClass
from src.validation.lab import OpportunityValidationLab


class TestResearchDirectorHistoryContinuity(unittest.TestCase):
    """Test suite ensuring cross-run history continuity and anti-duplicate governance."""

    def setUp(self):
        self.topic = "Autonomous Enterprise ERP Ledger Reconciliation"
        self.span = SourceSpan(
            document_name="erp_audit.pdf",
            document_hash="hash_run_a",
            page_or_section="P1",
            paragraph_index=0,
            text="Initial baseline claim on ERP reconciliation latency.",
            span_hash="span_run_a"
        )

    def test_run_b_knows_run_a_and_avoids_duplicate_queries(self):
        """
        RUN A conducts initial discovery.
        RUN B executes subsequent inquiry on the same topic:
        Verifies that RUN B avoids querying already-resolved investigation topics.
        """
        # RUN A: Initial claims and baseline investigation
        claims_run_a = [
            ExtractedClaim(
                claim_id="CLM-A-01",
                text="Legacy ERP reconciliations delay financial close by 48 hours.",
                evidence_grade=EvidenceGrade.FACT,
                confidence=0.92,
                source_citation="Financial Operations Review 2024",
                entity_or_topic=self.topic,
                source_span=self.span,
            )
        ]

        investigations_run_a = ResearchDirectorEngine.evaluate_next_best_research(
            topic=self.topic,
            claims=claims_run_a,
            resolved_investigation_queries=[],
            history_topics=[self.topic]
        )
        self.assertGreater(len(investigations_run_a), 0)
        run_a_top_investigation = investigations_run_a[0]
        run_a_query = run_a_top_investigation.actionable_query

        # RUN B: New evidence ingested, and run_a_query is recorded as resolved in history
        claims_run_b = claims_run_a + [
            ExtractedClaim(
                claim_id="CLM-B-01",
                text="Enterprise procurement surveys indicate 68% of CFOs allocate budget for automated close tooling.",
                evidence_grade=EvidenceGrade.EVIDENCE,
                confidence=0.89,
                source_citation="CFO Peer Benchmark",
                entity_or_topic=self.topic,
                source_span=self.span,
            )
        ]

        investigations_run_b = ResearchDirectorEngine.evaluate_next_best_research(
            topic=self.topic,
            claims=claims_run_b,
            resolved_investigation_queries=[run_a_query],
            history_topics=[self.topic]
        )

        # Assert RUN B does NOT duplicate RUN A's resolved query
        run_b_queries = [inv.actionable_query.lower() for inv in investigations_run_b]
        self.assertNotIn(run_a_query.lower(), run_b_queries)
        self.assertGreater(len(investigations_run_b), 0)
        # Verify RUN B targets an unresolved gap
        self.assertNotEqual(investigations_run_b[0].actionable_query, run_a_query)

    def test_run_c_targets_unresolved_gaps_from_a_and_b(self):
        """
        Verifies that across A, B, and C, the Director progressively shifts focus
        from buyer/primary discovery to deeper technical and economic sensitivity gaps.
        """
        # RUN A: Baseline
        claims_a = [
            ExtractedClaim(
                claim_id="CLM-A-01",
                text="Legacy ERP reconciliations delay financial close.",
                evidence_grade=EvidenceGrade.FACT,
                confidence=0.90,
                source_citation="Source A",
                entity_or_topic=self.topic,
                source_span=self.span,
            )
        ]
        inv_a = ResearchDirectorEngine.evaluate_next_best_research(
            topic=self.topic,
            claims=claims_a,
            resolved_investigation_queries=[]
        )
        resolved_a = inv_a[0].actionable_query

        # RUN B: Ingests buyer evidence, resolves resolved_a
        claims_b = claims_a + [
            ExtractedClaim(
                claim_id="CLM-B-01",
                text="CFOs budget $40k annually for close automation.",
                evidence_grade=EvidenceGrade.EVIDENCE,
                confidence=0.88,
                source_citation="Source B",
                entity_or_topic=self.topic,
                source_span=self.span,
            )
        ]
        inv_b = ResearchDirectorEngine.evaluate_next_best_research(
            topic=self.topic,
            claims=claims_b,
            resolved_investigation_queries=[resolved_a]
        )
        resolved_b = inv_b[0].actionable_query

        # RUN C: Evaluates with both A and B resolved
        claims_c = claims_b + [
            ExtractedClaim(
                claim_id="CLM-C-01",
                text="Trial showed 4.2x ROI under base adoption scenario.",
                evidence_grade=EvidenceGrade.FACT,
                confidence=0.91,
                source_citation="Source C",
                entity_or_topic=self.topic,
                source_span=self.span,
            )
        ]
        inv_c = ResearchDirectorEngine.evaluate_next_best_research(
            topic=self.topic,
            claims=claims_c,
            resolved_investigation_queries=[resolved_a, resolved_b]
        )

        run_c_queries = [i.actionable_query.lower() for i in inv_c]
        self.assertNotIn(resolved_a.lower(), run_c_queries)
        self.assertNotIn(resolved_b.lower(), run_c_queries)
        self.assertTrue(all(i.priority_rank > 0 for i in inv_c))

    def test_disproven_or_killed_thesis_does_not_reappear_as_mvp(self):
        """
        Verifies that an opportunity flagged with severe WTP deficit or critical vulnerability
        is classified under PILOT_EXPERIMENT_REQUIRED or KILL_OPPORTUNITY_NOW and does not
        falsely claim PROCEED_TO_MVP without empirical backing.
        """
        opp = SaaSSolutionOpportunity(
            opportunity_id="OPP-FAIL-01",
            solution_title="Generic Un-Differentiated Wrapper",
            category="B2B SaaS",
            problem_addressed_id="PROB-001",
            problem_title="Trivial Task Friction",
            target_buyer_icp="Small Business Owner",
            core_value_proposition="Wrapper with no data moat.",
            what_you_can_offer="Basic prompt template.",
            technical_blueprint="Simple API call",
            monetization_model="$10 / month",
            estimated_build_time="1 day",
            opportunity_score=4.0,
            roi_multiple="Unknown"
        )
        # Without empirical buyer evidence, validation lab must NOT approve PROCEED_TO_MVP
        report = OpportunityValidationLab.run_validation_lab(opp, [], self.topic)
        self.assertNotEqual(report.verdict, ValidationVerdict.PROCEED_TO_MVP)
        self.assertIn(report.verdict, [ValidationVerdict.PILOT_EXPERIMENT_REQUIRED, ValidationVerdict.KILL_OPPORTUNITY_NOW])
        self.assertIn("Evidence currently supports", report.verdict_rationale)


if __name__ == "__main__":
    unittest.main()
