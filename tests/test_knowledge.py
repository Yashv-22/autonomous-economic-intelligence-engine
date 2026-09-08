"""
Unit Tests for Knowledge Layer: Relational SQLite, InMemoryVectorStore, NetworkXGraphStore & KnowledgeManager.
"""

import os
import unittest
import tempfile
import gc
from src.models.schemas import (
    SourceSpan,
    ExtractedClaim,
    ContradictionRecord,
    ProblemHypothesis,
    EvidenceGrade,
    ContradictionType,
    AuditRecord,
)
from src.knowledge.relational import SQLiteRelationalStore
from src.knowledge.semantic import InMemoryVectorStore
from src.knowledge.graph import NetworkXGraphStore
from src.knowledge.manager import KnowledgeManager


class TestKnowledgeLayer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_knowledge.db")
        self.relational = SQLiteRelationalStore(db_path=self.db_path)
        self.semantic = InMemoryVectorStore()
        self.graph = NetworkXGraphStore()
        self.manager = KnowledgeManager(
            relational_store=self.relational,
            semantic_store=self.semantic,
            graph_store=self.graph,
        )

        # Sample test objects
        self.span1 = SourceSpan(
            document_name="doc1.pdf",
            document_hash="1111" * 16,
            page_or_section="Page 1",
            paragraph_index=0,
            text="McKinsey reports 88% enterprise GenAI adoption.",
            span_hash="aaaa" * 16,
        )
        self.span2 = SourceSpan(
            document_name="doc2.pdf",
            document_hash="2222" * 16,
            page_or_section="Page 2",
            paragraph_index=1,
            text="80% of enterprises report no material EBITDA earnings uplift.",
            span_hash="bbbb" * 16,
        )
        self.claim1 = ExtractedClaim(
            claim_id="CLAIM-0001",
            text="McKinsey reports 88% enterprise GenAI adoption.",
            entity_or_topic="Enterprise AI Adoption",
            evidence_grade=EvidenceGrade.EVIDENCE,
            institution="McKinsey",
            quantitative_metric="88%",
            source_span=self.span1,
            confidence_score=0.95,
            tags=["adoption"],
            polarity="POSITIVE",
        )
        self.claim2 = ExtractedClaim(
            claim_id="CLAIM-0002",
            text="80% of enterprises report no material EBITDA earnings uplift.",
            entity_or_topic="Economic & EBITDA Returns",
            evidence_grade=EvidenceGrade.EVIDENCE,
            institution="Analyst",
            quantitative_metric="80%",
            source_span=self.span2,
            confidence_score=0.92,
            tags=["ebitda"],
            polarity="NEGATIVE",
        )
        self.contradiction = ContradictionRecord(
            contradiction_id="CONTRA-0001",
            topic="The AI Productivity Paradox",
            claim_a=self.claim1,
            claim_b=self.claim2,
            contradiction_type=ContradictionType.PROJECTION_VS_REALITY,
            explanation="Adoption does not translate into bottom-line EBITDA gains.",
            severity=9.0,
        )
        self.hypothesis = ProblemHypothesis(
            hypothesis_id="HYPO-0001",
            title="Velocity Drift at Handoffs",
            statement="Accelerating upstream velocity without redesigning handoffs causes queue congestion.",
            null_hypothesis="H0: Upstream AI acceleration proportionally reduces cycle times.",
            supporting_claim_ids=["CLAIM-0001"],
            opposing_claim_ids=[],
            affected_functions=["Marketing", "Legal"],
            falsification_criteria="Audited turnaround time before/after across 50 value streams.",
            confidence_score=0.90,
        )

    def tearDown(self):
        gc.collect()
        self.temp_dir.cleanup()

    def test_relational_persistence_and_query(self):
        """Verify SQLite relational store saves and retrieves all items."""
        self.relational.persist_all(
            [self.span1, self.span2],
            [self.claim1, self.claim2],
            [self.contradiction],
            [self.hypothesis],
        )

        claims = self.relational.get_claims()
        self.assertEqual(len(claims), 2)
        self.assertEqual(claims[0].claim_id, "CLAIM-0001")
        self.assertEqual(claims[0].source_span.document_name, "doc1.pdf")

        # Test audit log
        audit_rec = AuditRecord(
            audit_id="AUD-0001",
            correlation_id="CORR-123",
            timestamp="2026-09-04T00:00:00Z",
            action="TEST_ACTION",
            actor="Tester",
            input_hash="hash_in",
            output_hash="hash_out",
            metadata={"test": True},
            status="SUCCESS",
        )
        self.relational.log_audit_record(audit_rec)
        audit_logs = self.relational.get_audit_records("CORR-123")
        self.assertEqual(len(audit_logs), 1)
        self.assertEqual(audit_logs[0].action, "TEST_ACTION")

    def test_semantic_vector_store_similarity(self):
        """Verify vector index and similarity retrieval."""
        self.semantic.index_item("c1", "Enterprise adoption of generative AI reaches 88%", {"grade": "EVIDENCE"})
        self.semantic.index_item("c2", "Unrelated database indexing query optimization", {"grade": "FACT"})

        results = self.semantic.search_similar("Generative AI enterprise adoption", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "c1")
        self.assertGreater(results[0]["similarity"], 0.5)

    def test_graph_store_relations_and_paths(self):
        """Verify graph topology, node insertion, and path discovery."""
        self.graph.add_node("CLAIM-1", "CLAIM", {"text": "Upstream AI faster"})
        self.graph.add_node("CLAIM-2", "CLAIM", {"text": "Downstream queue grows"})
        self.graph.add_node("HYPO-1", "HYPOTHESIS", {"title": "Drift"})

        self.graph.add_edge("HYPO-1", "CLAIM-1", relation_type="SUPPORTED_BY")
        self.graph.add_edge("CLAIM-1", "CLAIM-2", relation_type="CAUSES")

        neighbors = self.graph.get_neighbors("HYPO-1", relation_type="SUPPORTED_BY")
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]["node_id"], "CLAIM-1")

        path = self.graph.get_causal_path("HYPO-1", "CLAIM-2")
        self.assertEqual(path, ["HYPO-1", "CLAIM-1", "CLAIM-2"])

    def test_knowledge_manager_sync(self):
        """Verify unified coordinator syncs across relational, vector, and graph layers."""
        self.manager.sync_all(
            [self.span1, self.span2],
            [self.claim1, self.claim2],
            [self.contradiction],
            [self.hypothesis],
        )

        # Relational check
        claims = self.manager.relational.get_claims()
        self.assertEqual(len(claims), 2)

        # Semantic check
        sem_res = self.manager.search_semantic_claims("GenAI adoption McKinsey", top_k=1)
        self.assertEqual(len(sem_res), 1)
        self.assertEqual(sem_res[0]["id"], "CLAIM-0001")

        # Graph lineage check
        lineage = self.manager.get_claim_lineage("CLAIM-0001")
        self.assertEqual(lineage["claim_id"], "CLAIM-0001")
        self.assertGreater(len(lineage["connected_elements"]), 0)


if __name__ == "__main__":
    unittest.main()
