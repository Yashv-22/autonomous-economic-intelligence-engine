"""
Hierarchical Research Orchestrator.
Coordinates specialized agents, shared blackboard, knowledge persistence, and audit trail generation.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from src.models.schemas import (
    ResearchObjective,
    ProblemDossier,
    AuditRecord,
)
from src.agents.base import AgentContext
from src.agents.director import ResearchDirectorAgent
from src.agents.ingestion import IngestionAgent
from src.agents.extractor import ClaimExtractorAgent
from src.agents.validator import ValidationCriticAgent
from src.agents.synthesizer import SynthesizerAgent
from src.knowledge.manager import KnowledgeManager
from src.orchestration.blackboard import ResearchBlackboard
from src.core.identifiers import generate_uuid, compute_sha256
from src.core.logging import logger, correlation_id_ctx, task_id_ctx
from src.core.events import event_bus, SystemEvent


class HierarchicalOrchestrator:
    """Master orchestrator executing autonomous operating-model research workflows."""

    def __init__(
        self,
        knowledge_manager: Optional[KnowledgeManager] = None,
    ):
        self.knowledge_manager = knowledge_manager or KnowledgeManager()

        # Instantiate specialized agents
        self.director_agent = ResearchDirectorAgent()
        self.ingestion_agent = IngestionAgent()
        self.extractor_agent = ClaimExtractorAgent()
        self.validator_agent = ValidationCriticAgent()
        self.synthesizer_agent = SynthesizerAgent()

    def execute_research_workflow(
        self,
        objective: ResearchObjective,
        local_dir: Optional[str] = None,
        output_dir: str = "output",
        correlation_id: Optional[str] = None,
    ) -> ProblemDossier:
        """
        Execute full autonomous vertical slice from objective to synthesis and audit trail.
        """
        cid = correlation_id or generate_uuid()
        task_id = f"TASK-{generate_uuid()[:8].upper()}"
        run_id = getattr(objective, "run_id", None) or f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        objective.run_id = run_id

        correlation_id_ctx.set(cid)
        task_id_ctx.set(task_id)

        blackboard = ResearchBlackboard(
            task_id=task_id,
            correlation_id=cid,
            run_id=run_id,
            objective=objective,
        )

        context = AgentContext(
            task_id=task_id,
            correlation_id=cid,
            run_id=run_id,
            shared_blackboard=blackboard.model_dump(),
        )

        logger.info(f"Initiating research workflow [{task_id}] (Run ID: {run_id}) for objective: '{objective.query}'")
        event_bus.publish(
            SystemEvent(
                event_type="RESEARCH_WORKFLOW_STARTED",
                correlation_id=cid,
                task_id=task_id,
                payload={"query": objective.query, "topic": objective.topic, "run_id": run_id},
            )
        )

        # 1. Strategy & Query Decomposition (ResearchDirector)
        queries = self.director_agent.run(context, objective=objective)
        blackboard.search_queries = queries
        logger.info(f"[1/6] Director generated {len(queries)} research queries.")

        # 2. Source Acquisition & Cryptographic Ingestion (IngestionAgent)
        spans = self.ingestion_agent.run(context, local_dir=local_dir, search_queries=queries)
        for s in spans:
            s.run_id = run_id
        blackboard.spans = spans
        merkle_root = self.ingestion_agent.provenance_ledger.compute_merkle_root()
        blackboard.merkle_provenance_root = merkle_root
        logger.info(f"[2/6] Ingestion acquired {len(spans)} spans. Merkle Root: {merkle_root[:12]}...")

        # 3. Structured Claim Extraction & Epistemic Grading (ClaimExtractorAgent)
        claims = self.extractor_agent.run(context, spans=spans)
        for c in claims:
            c.run_id = run_id
        blackboard.claims = claims
        logger.info(f"[3/6] Extraction produced {len(claims)} structured claims.")

        # 4. Contradiction Detection & Problem Hypotheses (ValidationCriticAgent)
        contradictions, hypotheses = self.validator_agent.run(context, claims=claims)
        for k in contradictions:
            k.run_id = run_id
        for h in hypotheses:
            h.run_id = run_id
        blackboard.contradictions = contradictions
        blackboard.hypotheses = hypotheses
        logger.info(f"[4/6] Identified {len(contradictions)} tensions and {len(hypotheses)} hypotheses.")

        # 5. Gap Detection & Evidence-Backed Synthesis (Director + SynthesizerAgent)
        gaps = self.director_agent.detect_research_gaps(context, objective, len(claims))
        blackboard.gaps = gaps

        synthesis = self.synthesizer_agent.run(
            context,
            objective=objective,
            claims=claims,
            contradictions=contradictions,
            hypotheses=hypotheses,
            gaps=gaps,
        )
        blackboard.synthesis = synthesis
        logger.info(f"[5/6] Synthesizer generated grounded synthesis (Confidence: {synthesis.epistemic_confidence * 100:.1f}%).")

        # 6. Synchronous Knowledge Layer Updates & Dossier Export
        self.knowledge_manager.sync_all(spans, claims, contradictions, hypotheses, run_id=run_id)

        # Count claims by epistemic grade
        grade_counts: Dict[str, int] = {}
        for c in claims:
            g = c.evidence_grade.value
            grade_counts[g] = grade_counts.get(g, 0) + 1

        doc_count = len(set(s.document_name for s in spans))
        dossier = ProblemDossier(
            dossier_id=f"DOSSIER-{uuid.uuid4().hex[:8].upper()}",
            run_id=run_id,
            title=f"Operating Model Intelligence Dossier: {objective.topic}",
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_documents_ingested=doc_count,
            total_claims_extracted=len(claims),
            claims_by_grade=grade_counts,
            verified_contradictions=contradictions,
            hypothesized_problems=hypotheses,
            merkle_provenance_root=merkle_root,
            synthesis=synthesis,
        )

        json_path = os.path.join(output_dir, "claims_ledger.json")
        md_path = os.path.join(output_dir, "problem_dossier.md")
        self.knowledge_manager.relational.export_json_ledger(dossier, output_path=json_path)
        self.knowledge_manager.relational.export_markdown_dossier(dossier, output_path=md_path)

        # Record immutable audit record
        audit_rec = AuditRecord(
            audit_id=f"AUD-{generate_uuid()[:8].upper()}",
            correlation_id=cid,
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            action="EXECUTE_RESEARCH_WORKFLOW",
            actor="HierarchicalOrchestrator",
            input_hash=compute_sha256(objective.model_dump_json()),
            output_hash=compute_sha256(dossier.model_dump_json()),
            metadata={
                "task_id": task_id,
                "run_id": run_id,
                "total_claims": len(claims),
                "total_spans": len(spans),
                "contradictions_count": len(contradictions),
                "hypotheses_count": len(hypotheses),
                "merkle_root": merkle_root,
            },
            status="SUCCESS",
        )
        self.knowledge_manager.relational.log_audit_record(audit_rec)

        event_bus.publish(
            SystemEvent(
                event_type="RESEARCH_WORKFLOW_COMPLETED",
                correlation_id=cid,
                task_id=task_id,
                payload={"dossier_id": dossier.dossier_id, "claims_extracted": len(claims), "run_id": run_id},
            )
        )

        logger.info(f"[6/6] Workflow complete. Exported dossiers to '{output_dir}'.")
        return dossier
