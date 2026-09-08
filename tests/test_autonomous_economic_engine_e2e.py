"""
The Ultimate Unbroken End-to-End Integration Gate Test.
Tests the full progression of the Autonomous Economic Intelligence & Opportunity Engine:

USER OBJECTIVE
    ↓
DIRECTOR / AUTONOMOUS RESEARCH ENGINE
    ↓
QUERY GENERATION
    ↓
AGENT REACH & INTERNET PIPELINE
    ↓
SOURCE ACQUISITION & NORMALIZATION
    ↓
PROVENANCE (MERKLE LEDGER REGISTRATION)
    ↓
CLAIMS (EPISTEMIC CLASSIFICATION)
    ↓
CONTRADICTION & GAP ANALYSIS
    ↓
KNOWLEDGE GRAPH HYDRATION
    ↓
SYNTHESIS & PROBLEM DISCOVERY
    ↓
OPPORTUNITY DISCOVERY & RANKING (CALIBRATED I_opp)
    ↓
SOLUTION ARCHITECTURE BLUEPRINT
    ↓
ADVERSARIAL VALIDATION ("DO NOT BUILD YET" / EXPERIMENT TEST)
    ↓
EXECUTIVE DASHBOARD DATA INTEGRITY
"""

import os
import shutil
import tempfile
import unittest

from src.models.schemas import ResearchObjective, EvidenceGrade
from src.research.discovery.engine import AutonomousResearchEngine
from src.internet.pipeline import InternetAcquisitionPipeline
from src.internet.discovery.engine import DiscoveryEngine
from src.internet.acquisition.engine import AcquisitionEngine
from src.internet.normalization.engine import NormalizationEngine
from src.internet.provenance.tracker import InternetProvenanceTracker
from src.internet.providers.mock_provider import MockSearchProvider, MockFetchProvider
from src.internet.search.engine import MultiProviderSearchEngine
from src.storage.raw_corpus import RawCorpusManager
from src.storage.normalized_corpus import NormalizedCorpusManager
from src.research.memory.session_store import ResearchSessionStore
from src.opportunity.engine import OpportunityDiscoveryEngine
from src.opportunity.schemas import ValidationVerdict, EpistemicCertainty
from fastapi.testclient import TestClient
from src.server.app import app


class TestAutonomousEconomicEngineE2E(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.raw_dir = os.path.join(self.temp_dir, "raw")
        self.norm_dir = os.path.join(self.temp_dir, "normalized")
        self.sess_dir = os.path.join(self.temp_dir, "sessions")

        # Mock internet discovery and fetching for rapid deterministic testing
        self.mock_search = MultiProviderSearchEngine(
            primary_provider=MockSearchProvider(),
            secondary_providers=[],
            fallback_to_mock=True,
        )

        self.research_engine = AutonomousResearchEngine(
            search_engine=self.mock_search,
            fetcher=MockFetchProvider(),
            raw_corpus=RawCorpusManager(base_dir=self.raw_dir),
            normalized_corpus=NormalizedCorpusManager(base_dir=self.norm_dir),
            session_store=ResearchSessionStore(base_dir=self.sess_dir),
        )

        self.opportunity_engine = OpportunityDiscoveryEngine()
        self.client = TestClient(app)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_autonomous_economic_engine_pipeline(self):
        """
        Execute the full unbroken lifecycle from User Objective down to
        Executive Dashboard and Adversarial Blueprint Validation.
        """
        # 1. USER OBJECTIVE
        topic = "Enterprise AI Operating Model Redesign"
        query = "Analyze enterprise AI operating model transformation bottlenecks, straight-through routing, and EBITDA returns"
        objective = ResearchObjective(
            objective_id="OBJ-E2E-GATE",
            query=query,
            topic=topic,
            max_depth=2,
            budget_sources=5,
        )
        self.assertEqual(objective.topic, topic)
        self.assertIn("straight-through routing", objective.query)

        # 2. INTERNET PIPELINE (Agent Reach + Normalization + Provenance)
        internet_pipeline = InternetAcquisitionPipeline(
            discovery=DiscoveryEngine(search_engine=self.mock_search),
            acquisition=AcquisitionEngine(fetcher=MockFetchProvider()),
            normalization=NormalizationEngine(),
            provenance_tracker=InternetProvenanceTracker(),
        )
        source_spans = internet_pipeline.execute(queries=[objective.query], max_sources=3)
        self.assertGreater(len(source_spans), 0)
        self.assertIsNotNone(source_spans[0].span_hash)

        # 3. RESEARCH CYCLE (Director → Ingestion → Provenance → Claims → Contradictions → Graph)
        dossier = self.research_engine.execute_research(
            objective=objective,
            local_dir=None,
            max_iterations=1,
            budget_sources=3,
            output_dir=self.output_dir,
        )
        self.assertIsNotNone(dossier)
        self.assertGreater(dossier.total_claims_extracted, 0)
        self.assertIsNotNone(dossier.merkle_provenance_root)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "problem_dossier.md")))

        # 4. KNOWLEDGE & CLAIMS VERIFICATION
        claims = self.research_engine.km.relational.get_claims()
        self.assertGreater(len(claims), 0)
        valid_grades = [
            EvidenceGrade.FACT,
            EvidenceGrade.EVIDENCE,
            EvidenceGrade.INFERENCE,
            EvidenceGrade.HYPOTHESIS,
            EvidenceGrade.ASSUMPTION,
            EvidenceGrade.RECOMMENDATION,
        ]
        for c in claims[:5]:
            self.assertIn(c.evidence_grade, valid_grades)
            self.assertIsNotNone(c.source_span.span_hash)

        # 5. MULTI-ENTITY KNOWLEDGE GRAPH TOPOLOGY
        graph_data = self.research_engine.km.graph.get_full_graph_data(limit_nodes=50)
        self.assertIn("nodes", graph_data)
        self.assertIn("edges", graph_data)

        # 6. ECONOMIC OPPORTUNITY DISCOVERY (Problems + SaaS Solutions)
        matrix = self.opportunity_engine.discover_opportunities(claims=claims, topic=topic)
        self.assertGreater(matrix.total_problems_identified, 0)
        self.assertGreater(matrix.total_solutions_generated, 0)
        self.assertGreater(len(matrix.solution_opportunities), 0)

        # 7. #1 RANKED OPPORTUNITY INSPECTION ($I_opp, Rationale, 8 Dimensions)
        ranked_opps = sorted(matrix.solution_opportunities, key=lambda o: o.opportunity_score, reverse=True)
        top_opp = ranked_opps[0]
        self.assertGreaterEqual(top_opp.opportunity_score, 7.0)
        self.assertIsNotNone(top_opp.score_breakdown)
        self.assertIsNotNone(top_opp.score_breakdown.label)
        self.assertIsNotNone(top_opp.score_breakdown.ranking_rationale)
        self.assertTrue(len(top_opp.score_breakdown.ranking_rationale) > 0)
        
        # Verify 8 Inspectable Dimensions
        dims = top_opp.score_breakdown.dimensions
        self.assertIn(dims.demand_evidence, ["Strong", "Moderate", "Weak"])
        self.assertIn(dims.problem_severity, ["Critical", "High", "Moderate", "Low"])
        self.assertIn(dims.wtp_evidence, ["Strong", "Moderate", "Speculative"])
        self.assertIn(dims.competition_intensity, ["High", "Moderate", "Low"])
        self.assertIn(dims.competitive_gap, ["Large", "Moderate", "Narrow"])
        self.assertIn(dims.technical_feasibility, ["High", "Moderate", "Challenging"])
        self.assertIn(dims.defensibility, ["High", "Moderate", "Low"])
        self.assertIn(dims.evidence_quality, ["High", "Moderate", "Low"])

        # 8. HARD EPISTEMIC EVIDENCE BOUNDARY
        self.assertIn("FACT", top_opp.epistemic_breakdown)
        self.assertIn("INFERENCE", top_opp.epistemic_breakdown)
        self.assertIn("HYPOTHESIS", top_opp.epistemic_breakdown)
        self.assertGreater(len(top_opp.epistemic_breakdown["FACT"]), 0)

        # 9. SOLUTION ARCHITECTURE BLUEPRINT
        blueprint = top_opp.blueprint
        self.assertIsNotNone(blueprint)
        self.assertIsNotNone(blueprint.concept)
        self.assertIsNotNone(blueprint.technical_architecture)
        self.assertGreater(len(blueprint.integrations), 0)
        self.assertIsNotNone(blueprint.mvp_specification)
        self.assertIsNotNone(blueprint.pricing_hypotheses)
        self.assertIsNotNone(blueprint.estimated_build_time)

        # 10. ADVERSARIAL VALIDATION REPORT & VERDICT
        val_report = top_opp.validation_report
        self.assertIsNotNone(val_report)
        self.assertIn(val_report.verdict, [
            ValidationVerdict.PROCEED_TO_MVP,
            ValidationVerdict.PILOT_EXPERIMENT_REQUIRED,
            ValidationVerdict.DO_NOT_BUILD_YET,
        ])
        self.assertGreater(len(val_report.graveyard_failed_attempts), 0)
        self.assertIsNotNone(val_report.verdict_rationale)

        # 11. EXECUTIVE DASHBOARD DATA INTEGRITY VIA HTTP API
        res_status = self.client.get("/api/status")
        self.assertEqual(res_status.status_code, 200)
        self.assertEqual(res_status.json()["status"], "HEALTHY")

        res_opps = self.client.get("/api/opportunities")
        self.assertEqual(res_opps.status_code, 200)
        opps_data = res_opps.json()["solution_opportunities"]
        self.assertGreater(len(opps_data), 0)

        first_opp_id = opps_data[0]["opportunity_id"]
        res_sol = self.client.get(f"/api/solutions/{first_opp_id}")
        self.assertEqual(res_sol.status_code, 200)
        self.assertIn("technical_architecture", res_sol.json())

        res_val = self.client.get(f"/api/opportunities/{first_opp_id}/validate")
        self.assertEqual(res_val.status_code, 200)
        self.assertIn("verdict", res_val.json())

        res_gw = self.client.get("/api/gateway/status")
        self.assertEqual(res_gw.status_code, 200)
        self.assertIn("active_provider", res_gw.json())

        res_index = self.client.get("/")
        self.assertEqual(res_index.status_code, 200)
        self.assertIn("Autonomous Economic Intelligence", res_index.text)


if __name__ == "__main__":
    unittest.main()
