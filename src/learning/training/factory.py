"""
Provenance-Backed Training Data Factory.
Converts validated knowledge, extraction pairs, contradictions, and experiences into versioned JSONL training datasets.
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.models.schemas import ExtractedClaim, ContradictionRecord, ProblemHypothesis, SynthesisResult
from src.core.identifiers import generate_prefixed_id, compute_sha256
from src.core.logging import logger


class TrainingExample(BaseModel):
    example_id: str
    task_category: str
    system_prompt: str
    user_prompt: str
    target_response: str
    provenance_span_hash: Optional[str] = None
    source_document: Optional[str] = None
    epistemic_grade: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DatasetManifest(BaseModel):
    dataset_version: str
    created_at: str
    total_examples: int
    task_distribution: Dict[str, int]
    dataset_hash: str
    storage_path: str


class TrainingDataFactory:
    """Generates standardized, fine-tuning-ready JSONL datasets from accumulated operating model intelligence."""

    def __init__(self, output_dir: str = "data/training_datasets"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_dataset_from_knowledge(
        self,
        claims: List[ExtractedClaim],
        contradictions: List[ContradictionRecord],
        hypotheses: List[ProblemHypothesis],
        version: Optional[str] = None,
    ) -> DatasetManifest:
        """Construct a complete, multi-task supervised fine-tuning dataset."""
        version_id = version or f"dataset-v{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        examples: List[TrainingExample] = []
        task_dist: Dict[str, int] = {}

        # 1. Claim Extraction & Classification Examples
        for c in claims:
            user_prompt = f"Analyze the following enterprise text and extract the atomic claim along with its epistemic classification:\n\nText: \"{c.source_span.text}\""
            target = json.dumps({
                "claim_text": c.text,
                "epistemic_grade": c.evidence_grade.value,
                "institution": c.institution,
                "quantitative_metric": c.quantitative_metric,
                "polarity": c.polarity.value,
            }, indent=2)

            ex = TrainingExample(
                example_id=generate_prefixed_id("TRAIN"),
                task_category="claim_extraction_and_grading",
                system_prompt="You are an expert research analyst evaluating epistemic rigor and empirical evidence in operating model research.",
                user_prompt=user_prompt,
                target_response=target,
                provenance_span_hash=c.source_span.span_hash,
                source_document=c.source_span.document_name,
                epistemic_grade=c.evidence_grade.value,
            )
            examples.append(ex)
            task_dist["claim_extraction_and_grading"] = task_dist.get("claim_extraction_and_grading", 0) + 1

        # 2. Contradiction Detection Examples
        for k in contradictions:
            user_prompt = (
                f"Evaluate if there is an analytical contradiction between Claim A and Claim B:\n"
                f"Claim A: \"{k.claim_a.text}\" (Source: {k.claim_a.institution or 'Source A'})\n"
                f"Claim B: \"{k.claim_b.text}\" (Source: {k.claim_b.institution or 'Source B'})"
            )
            target = json.dumps({
                "has_contradiction": True,
                "contradiction_type": k.contradiction_type.value,
                "severity": k.severity,
                "synthesis_explanation": k.explanation,
            }, indent=2)

            ex = TrainingExample(
                example_id=generate_prefixed_id("TRAIN"),
                task_category="contradiction_detection",
                system_prompt="You are an adversarial validation critic detecting cross-source tensions and preserving analytical disagreement.",
                user_prompt=user_prompt,
                target_response=target,
                provenance_span_hash=k.claim_a.source_span.span_hash,
                source_document=k.claim_a.source_span.document_name,
            )
            examples.append(ex)
            task_dist["contradiction_detection"] = task_dist.get("contradiction_detection", 0) + 1

        # 3. Falsifiable Hypothesis Formulation Examples
        for h in hypotheses:
            user_prompt = f"Formulate a formal, falsifiable problem hypothesis regarding: \"{h.title}\""
            target = json.dumps({
                "statement": h.statement,
                "null_hypothesis": h.null_hypothesis,
                "affected_functions": h.affected_functions,
                "falsification_criteria": h.falsification_criteria,
            }, indent=2)

            ex = TrainingExample(
                example_id=generate_prefixed_id("TRAIN"),
                task_category="hypothesis_formulation",
                system_prompt="You are a scientific operating model researcher formulating testable hypotheses with strict null hypotheses and empirical disproof criteria.",
                user_prompt=user_prompt,
                target_response=target,
            )
            examples.append(ex)
            task_dist["hypothesis_formulation"] = task_dist.get("hypothesis_formulation", 0) + 1

        # Write to JSONL
        out_file = os.path.join(self.output_dir, f"{version_id}.jsonl")
        lines = [json.dumps(e.dict()) for e in examples]
        with open(out_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        # Manifest
        content_hash = compute_sha256("\n".join(lines))
        manifest = DatasetManifest(
            dataset_version=version_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            total_examples=len(examples),
            task_distribution=task_dist,
            dataset_hash=content_hash,
            storage_path=out_file,
        )

        manifest_path = os.path.join(self.output_dir, f"{version_id}.manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.dict(), f, indent=2)

        logger.info(f"TrainingDataFactory: Generated dataset '{manifest.dataset_version}' with {len(examples)} examples.")
        return manifest

    def generate_sft_dataset(
        self,
        claims: List[ExtractedClaim],
        contradictions: Optional[List[ContradictionRecord]] = None,
        hypotheses: Optional[List[ProblemHypothesis]] = None,
        topic_filter: Optional[str] = None,
        version: Optional[str] = None,
    ) -> DatasetManifest:
        """Alias for generate_dataset_from_knowledge."""
        return self.generate_dataset_from_knowledge(
            claims=claims,
            contradictions=contradictions or [],
            hypotheses=hypotheses or [],
            version=version,
        )
