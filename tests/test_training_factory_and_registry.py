"""
Unit tests for Training Data Factory, Model Registry, and Evaluation Gate.
"""

import unittest
import tempfile
import os
import json

from src.learning.training.factory import TrainingDataFactory
from src.learning.models.registry import ModelRegistry
from src.learning.evaluation.gate import EvaluationGate
from src.models.schemas import ExtractedClaim, SourceSpan, EvidenceGrade, PolarityType, ContradictionRecord, ContradictionType, ProblemHypothesis
from src.core.identifiers import compute_sha256


class TestTrainingFactoryAndRegistry(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.factory = TrainingDataFactory(output_dir=os.path.join(self.temp_dir, "datasets"))
        self.registry = ModelRegistry(registry_file=os.path.join(self.temp_dir, "registry.json"))

    def test_training_dataset_generation(self):
        span = SourceSpan(
            document_name="doc.pdf",
            document_hash="hash1",
            page_or_section="Page 1",
            paragraph_index=0,
            text="McKinsey finds 88% adoption but 22% EBITDA impact.",
            span_hash=compute_sha256("McKinsey finds 88% adoption but 22% EBITDA impact."),
        )
        claim = ExtractedClaim(
            claim_id="CLAIM-0001",
            text="88% adoption coexists with 22% EBITDA impact.",
            entity_or_topic="AI Economics",
            evidence_grade=EvidenceGrade.EVIDENCE,
            institution="McKinsey",
            quantitative_metric="88%",
            source_span=span,
            confidence_score=0.95,
            polarity=PolarityType.POSITIVE,
        )
        contra = ContradictionRecord(
            contradiction_id="CONTRA-0001",
            topic="AI Adoption vs Return",
            claim_a=claim,
            claim_b=claim,
            contradiction_type=ContradictionType.PROJECTION_VS_REALITY,
            explanation="Near-universal adoption with negligible earnings impact.",
            severity=9.0,
        )
        hypo = ProblemHypothesis(
            hypothesis_id="HYPO-0001",
            title="Adoption Paradox",
            statement="Piecemeal adoption without redesign fails.",
            null_hypothesis="H0: Localized adoption produces proportional enterprise return.",
            falsification_criteria="Measure 100 enterprise value streams.",
            affected_functions=["Operations"],
        )

        manifest = self.factory.generate_dataset_from_knowledge(
            claims=[claim],
            contradictions=[contra],
            hypotheses=[hypo],
            version="test-dataset-v1",
        )

        self.assertEqual(manifest.total_examples, 3)
        self.assertTrue(os.path.exists(manifest.storage_path))

    def test_model_registry_and_evaluation_gate(self):
        candidate = self.registry.register_model_version(
            base_model="gemini-1.5-pro",
            dataset_version="test-dataset-v1",
            training_run_id="run-001",
            evaluation_scores={
                "grounding_accuracy": 0.90,
                "hallucination_rate": 0.03,
                "contradiction_recall": 0.85,
                "adversarial_injection_resistance": 0.98,
            },
        )
        self.assertEqual(candidate.model_version_id, "model-v001")
        self.assertEqual(candidate.deployment_status, "CANDIDATE")

        # Evaluate candidate
        verdict = EvaluationGate.evaluate_candidate(
            model_version_id=candidate.model_version_id,
            evaluation_scores=candidate.evaluation_scores,
        )
        self.assertTrue(verdict.passed_all_gates)
        self.assertEqual(verdict.decision, "PROMOTED_TO_PRODUCTION")

        # Promote
        promoted = self.registry.promote_to_production("model-v001")
        self.assertTrue(promoted)
        prod = self.registry.get_production_model()
        self.assertEqual(prod.model_version_id, "model-v001")


if __name__ == "__main__":
    unittest.main()
