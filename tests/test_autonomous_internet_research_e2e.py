"""
End-to-End Integration Test for Autonomous Internet Research & Continuous Learning.
"""

import unittest
import tempfile
import os
import shutil

from src.models.schemas import ResearchObjective
from src.research.discovery.engine import AutonomousResearchEngine
from src.internet.providers.mock_provider import MockSearchProvider, MockFetchProvider
from src.internet.search.engine import MultiProviderSearchEngine
from src.knowledge.manager import KnowledgeManager
from src.storage.raw_corpus import RawCorpusManager
from src.storage.normalized_corpus import NormalizedCorpusManager
from src.research.memory.session_store import ResearchSessionStore
from src.learning.training.factory import TrainingDataFactory
from src.learning.models.registry import ModelRegistry
from src.learning.evaluation.gate import EvaluationGate


class TestAutonomousInternetResearchE2E(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.raw_dir = os.path.join(self.temp_dir, "raw")
        self.norm_dir = os.path.join(self.temp_dir, "normalized")
        self.sess_dir = os.path.join(self.temp_dir, "sessions")
        self.data_dir = os.path.join(self.temp_dir, "datasets")

        self.mock_search = MultiProviderSearchEngine(
            primary_provider=MockSearchProvider(),
            secondary_providers=[],
            fallback_to_mock=True,
        )

        self.engine = AutonomousResearchEngine(
            search_engine=self.mock_search,
            fetcher=MockFetchProvider(),
            raw_corpus=RawCorpusManager(base_dir=self.raw_dir),
            normalized_corpus=NormalizedCorpusManager(base_dir=self.norm_dir),
            session_store=ResearchSessionStore(base_dir=self.sess_dir),
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_autonomous_research_end_to_end_loop(self):
        objective = ResearchObjective(
            objective_id="OBJ-E2E-TEST",
            query="Analyze enterprise AI operating model transformation bottlenecks, straight-through routing, and EBITDA returns",
            topic="Enterprise AI Operating Model Redesign",
            max_depth=2,
            budget_sources=5,
        )

        # 1. Execute Research
        dossier = self.engine.execute_research(
            objective=objective,
            local_dir=None,  # test pure internet discovery without local docs
            max_iterations=1,
            budget_sources=3,
            output_dir=self.output_dir,
        )

        self.assertIsNotNone(dossier)
        self.assertGreater(dossier.total_claims_extracted, 0)
        self.assertIsNotNone(dossier.merkle_provenance_root)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "problem_dossier.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "claims_ledger.json")))

        # 2. Verify Session Memory Checkpoint
        session = self.engine.session_store.create_or_load_session(topic="Enterprise AI Operating Model Redesign")
        self.assertGreater(len(session.executed_queries), 0)

        # 3. Generate Training Dataset
        factory = TrainingDataFactory(output_dir=self.data_dir)
        claims = self.engine.km.relational.get_claims()
        manifest = factory.generate_dataset_from_knowledge(
            claims=claims,
            contradictions=dossier.verified_contradictions,
            hypotheses=dossier.hypothesized_problems,
        )
        self.assertGreater(manifest.total_examples, 0)
        self.assertTrue(os.path.exists(manifest.storage_path))


if __name__ == "__main__":
    unittest.main()
