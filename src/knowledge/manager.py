"""
Unified Knowledge Manager.
Coordinates relational persistence, semantic retrieval, and graph topology synchronously.
"""

from typing import List, Dict, Any, Optional
from src.knowledge.interfaces import (
    RelationalStoreInterface,
    SemanticStoreInterface,
    GraphStoreInterface,
)
from src.knowledge.relational import SQLiteRelationalStore
from src.knowledge.semantic import InMemoryVectorStore
from src.knowledge.graph import NetworkXGraphStore
from src.models.schemas import (
    SourceSpan,
    ExtractedClaim,
    ContradictionRecord,
    ProblemHypothesis,
    AuditRecord,
    ProblemDossier,
)
from src.core.logging import logger


class KnowledgeManager:
    """Synchronized coordinator across Relational, Semantic, and Graph Knowledge Stores."""

    def __init__(
        self,
        relational_store: Optional[RelationalStoreInterface] = None,
        semantic_store: Optional[SemanticStoreInterface] = None,
        graph_store: Optional[GraphStoreInterface] = None,
        auto_hydrate: bool = True,
    ):
        self.relational = relational_store or SQLiteRelationalStore()
        self.semantic = semantic_store or InMemoryVectorStore()
        self.graph = graph_store or NetworkXGraphStore()
        if auto_hydrate:
            self.hydrate_from_db()

    def hydrate_from_db(self):
        """Hydrate in-memory vector store and graph store from persistent SQLite database."""
        try:
            claims = self.relational.get_claims()
            claims_to_hydrate = claims[:1000]
            for c in claims_to_hydrate:
                self.semantic.index_item(
                    item_id=c.claim_id,
                    text=c.text,
                    metadata={
                        "entity_or_topic": c.entity_or_topic,
                        "evidence_grade": c.evidence_grade.value,
                        "institution": c.institution,
                        "metric": c.quantitative_metric,
                        "span_hash": c.source_span.span_hash,
                    },
                )
                self.graph.add_node(
                    c.claim_id,
                    node_type="CLAIM",
                    properties={
                        "topic": c.entity_or_topic,
                        "grade": c.evidence_grade.value,
                        "metric": c.quantitative_metric,
                    },
                )
                self.graph.add_node(
                    c.source_span.span_hash,
                    node_type="SPAN",
                    properties={"doc": c.source_span.document_name, "section": c.source_span.page_or_section},
                )
                self.graph.add_edge(c.claim_id, c.source_span.span_hash, relation_type="DERIVED_FROM")

            # Hydrate contradictions & hypotheses if present
            from src.validation.contradiction import ContradictionDetector
            from src.validation.hypothesis import HypothesisGenerator
            detector = ContradictionDetector()
            contradictions = detector.detect_contradictions(claims_to_hydrate[:100])
            hypotheses = HypothesisGenerator.generate_hypotheses(claims_to_hydrate[:100], contradictions)

            for k in contradictions:
                self.graph.add_node(
                    k.contradiction_id,
                    node_type="CONTRADICTION",
                    properties={"topic": k.topic, "type": k.contradiction_type.value, "severity": k.severity},
                )
                self.graph.add_edge(k.contradiction_id, k.claim_a.claim_id, relation_type="TENSION_WITH")
                self.graph.add_edge(k.contradiction_id, k.claim_b.claim_id, relation_type="TENSION_WITH")

            for h in hypotheses:
                self.graph.add_node(
                    h.hypothesis_id,
                    node_type="HYPOTHESIS",
                    properties={"title": h.title},
                )
                for sc_id in h.supporting_claim_ids:
                    self.graph.add_edge(h.hypothesis_id, sc_id, relation_type="SUPPORTED_BY")
                for oc_id in h.opposing_claim_ids:
                    self.graph.add_edge(h.hypothesis_id, oc_id, relation_type="OPPOSED_BY")
                for fn in h.affected_functions:
                    fn_node_id = f"DEPT_{fn.upper().replace(' ', '_')}"
                    self.graph.add_node(fn_node_id, node_type="ORGANIZATION_FUNCTION")
                    self.graph.add_edge(h.hypothesis_id, fn_node_id, relation_type="AFFECTS")

            # Hydrate Economic Problems and Opportunities
            try:
                from src.opportunity.engine import OpportunityDiscoveryEngine
                opp_engine = OpportunityDiscoveryEngine()
                matrix = opp_engine.discover_opportunities(claims=claims)
                self.hydrate_opportunities(matrix)
            except Exception as opp_err:
                logger.debug(f"Opportunity graph hydration skipped: {opp_err}")

            logger.info(f"KnowledgeManager hydrated {len(claims)} claims and economic graph into Vector and Graph stores.")
        except Exception as e:
            logger.warning(f"Hydration from DB skipped or failed: {e}")

    def sync_all(
        self,
        spans: List[SourceSpan],
        claims: List[ExtractedClaim],
        contradictions: List[ContradictionRecord],
        hypotheses: List[ProblemHypothesis],
        run_id: Optional[str] = None,
    ) -> None:
        """
        Synchronously update relational, semantic, and graph layers atomically.
        """
        # 1. Relational Persistence
        self.relational.persist_all(spans, claims, contradictions, hypotheses, run_id=run_id)

        # 2. Semantic Vector Indexing (index top 300 claims for fast semantic search)
        for c in claims[:300]:
            self.semantic.index_item(
                item_id=c.claim_id,
                text=c.text,
                metadata={
                    "entity_or_topic": c.entity_or_topic,
                    "evidence_grade": c.evidence_grade.value,
                    "institution": c.institution,
                    "metric": c.quantitative_metric,
                    "span_hash": c.source_span.span_hash,
                },
            )

        # 3. Knowledge Graph Topology Construction (index top spans and claims for graph explorer)
        for s in spans[:200]:
            self.graph.add_node(
                s.span_hash,
                node_type="SPAN",
                properties={"doc": s.document_name, "section": s.page_or_section},
            )

        for c in claims[:300]:
            self.graph.add_node(
                c.claim_id,
                node_type="CLAIM",
                properties={
                    "topic": c.entity_or_topic,
                    "grade": c.evidence_grade.value,
                    "metric": c.quantitative_metric,
                },
            )
            # Edge: Span -> Claim (DERIVED_FROM)
            self.graph.add_edge(c.claim_id, c.source_span.span_hash, relation_type="DERIVED_FROM")

        for k in contradictions:
            self.graph.add_node(
                k.contradiction_id,
                node_type="CONTRADICTION",
                properties={"topic": k.topic, "type": k.contradiction_type.value, "severity": k.severity},
            )
            # Edges: Tension with Claim A & Claim B
            self.graph.add_edge(k.contradiction_id, k.claim_a.claim_id, relation_type="TENSION_WITH")
            self.graph.add_edge(k.contradiction_id, k.claim_b.claim_id, relation_type="TENSION_WITH")

        for h in hypotheses:
            self.graph.add_node(
                h.hypothesis_id,
                node_type="HYPOTHESIS",
                properties={"title": h.title},
            )
            for sc_id in h.supporting_claim_ids:
                self.graph.add_edge(h.hypothesis_id, sc_id, relation_type="SUPPORTED_BY")
            for oc_id in h.opposing_claim_ids:
                self.graph.add_edge(h.hypothesis_id, oc_id, relation_type="OPPOSED_BY")

            for fn in h.affected_functions:
                fn_node_id = f"DEPT_{fn.upper().replace(' ', '_')}"
                self.graph.add_node(fn_node_id, node_type="ORGANIZATION_FUNCTION")
                self.graph.add_edge(h.hypothesis_id, fn_node_id, relation_type="AFFECTS")

        logger.info(
            f"Knowledge synchronization complete: {len(spans)} spans, {len(claims)} claims, "
            f"{len(contradictions)} contradictions, {len(hypotheses)} hypotheses."
        )

    def search_semantic_claims(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search claims using vector similarity."""
        return self.semantic.search_similar(query, top_k=top_k)

    def get_claim_lineage(self, claim_id: str) -> Dict[str, Any]:
        """Trace full graph lineage for a specific claim."""
        neighbors = self.graph.get_neighbors(claim_id)
        return {
            "claim_id": claim_id,
            "connected_elements": neighbors,
        }

    def hydrate_opportunities(self, matrix):
        """Hydrate market problems, opportunities, and solution blueprints into graph."""
        if not matrix:
            return
        for prob in getattr(matrix, "market_problems", []):
            self.graph.add_node(
                prob.problem_id,
                node_type="MARKET_PROBLEM",
                properties={"title": prob.title, "severity": prob.severity_score, "segment": prob.target_segment},
            )
            for cid in getattr(prob, "cited_claims", []):
                if cid in self.graph.graph:
                    self.graph.add_edge(cid, prob.problem_id, relation_type="EVIDENCE_FOR")

        for opp in getattr(matrix, "solution_opportunities", []):
            self.graph.add_node(
                opp.opportunity_id,
                node_type="OPPORTUNITY",
                properties={"title": opp.solution_title, "score": opp.opportunity_score, "category": opp.category},
            )
            if opp.problem_addressed_id in self.graph.graph:
                self.graph.add_edge(opp.problem_addressed_id, opp.opportunity_id, relation_type="ADDRESSED_BY")
            if opp.blueprint:
                sol_id = f"SOL-{opp.opportunity_id.replace('OPP-', '')}"
                self.graph.add_node(
                    sol_id,
                    node_type="SOLUTION",
                    properties={"concept": opp.blueprint.concept, "icp": opp.blueprint.target_buyer_icp},
                )
                self.graph.add_edge(opp.opportunity_id, sol_id, relation_type="IMPLEMENTED_AS")
