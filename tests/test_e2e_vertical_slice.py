"""
Comprehensive End-to-End Test for the Autonomous AI Operating-Model Intelligence System Vertical Slice.
Verifies the complete pipeline from research objective to synthesis and audit trail.
"""

import os
import gc
import json
import unittest
import tempfile

from src.models.schemas import ResearchObjective
from src.research.loop import AutonomousResearchLoop
from src.orchestration.orchestrator import HierarchicalOrchestrator
from src.knowledge.manager import KnowledgeManager
from src.knowledge.relational import SQLiteRelationalStore


class TestE2EVerticalSlice(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = os.path.join(self.temp_dir.name, "output")
        self.db_path = os.path.join(self.output_dir, "test_vertical_slice.db")
        os.makedirs(self.output_dir, exist_ok=True)

        self.relational_store = SQLiteRelationalStore(db_path=self.db_path)
        self.knowledge_manager = KnowledgeManager(relational_store=self.relational_store)
        self.orchestrator = HierarchicalOrchestrator(knowledge_manager=self.knowledge_manager)
        self.research_loop = AutonomousResearchLoop(orchestrator=self.orchestrator)

    def tearDown(self):
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_full_vertical_slice_execution(self):
        """
        Execute end-to-end research loop from objective through discovery, ingestion,
        provenance, claim extraction, epistemic classification, contradiction detection,
        knowledge persistence, and grounded synthesis with audit trail.
        """
        objective = ResearchObjective(
            objective_id="OBJ-TEST-001",
            query="Analyze enterprise AI operating model redesign and straight-through routing bottlenecks",
            topic="Operating Model Transformation",
            max_depth=2,
            budget_sources=5,
        )

        dossier = self.research_loop.run_cycle(
            objective=objective,
            local_dir=".",
            max_iterations=1,
            output_dir=self.output_dir,
        )

        # 1. Verify Dossier Core Metrics
        self.assertIsNotNone(dossier)
        self.assertGreater(dossier.total_documents_ingested, 0)
        self.assertGreater(dossier.total_claims_extracted, 10)
        self.assertGreater(len(dossier.verified_contradictions), 0)
        self.assertGreater(len(dossier.hypothesized_problems), 0)
        self.assertEqual(len(dossier.merkle_provenance_root), 64)

        # 2. Verify Synthesis & Citations
        self.assertIsNotNone(dossier.synthesis)
        self.assertGreater(len(dossier.synthesis.detailed_findings), 0)
        self.assertGreater(len(dossier.synthesis.supporting_claim_ids), 0)
        self.assertGreater(len(dossier.synthesis.cited_span_hashes), 0)
        self.assertGreaterEqual(dossier.synthesis.epistemic_confidence, 0.70)

        # 3. Verify SQLite Relational Persistence
        claims_in_db = self.relational_store.get_claims()
        self.assertGreater(len(claims_in_db), 10)

        # 4. Verify Immutable Audit Trail
        audit_logs = self.relational_store.get_audit_records()
        self.assertGreater(len(audit_logs), 0)
        self.assertTrue(any(a.action == "EXECUTE_RESEARCH_WORKFLOW" for a in audit_logs))

        # 5. Verify Exported JSON & Markdown Files
        json_file = os.path.join(self.output_dir, "claims_ledger.json")
        md_file = os.path.join(self.output_dir, "problem_dossier.md")

        self.assertTrue(os.path.exists(json_file))
        self.assertTrue(os.path.exists(md_file))

        with open(json_file, "r", encoding="utf-8") as f:
            ledger_data = json.load(f)
        self.assertEqual(ledger_data["dossier_id"], dossier.dossier_id)

        with open(md_file, "r", encoding="utf-8") as f:
            md_text = f.read()
        self.assertIn("Operating Model Intelligence: Problem & Research Dossier", md_text)
        self.assertIn("Merkle Provenance Root", md_text)
        self.assertIn("Verified Cross-Source Analytical Contradictions", md_text)
        self.assertIn("Formulated Falsifiable Problem Hypotheses", md_text)


if __name__ == "__main__":
    unittest.main()
