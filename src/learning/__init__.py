"""
Continuous Learning Package.
Provides experience logging, training dataset generation, evaluation gates, and model versioning registry.
"""

from src.learning.experience.store import ExperienceStore, ExperienceRecord
from src.learning.training.factory import TrainingDataFactory, TrainingExample, DatasetManifest
from src.learning.models.registry import ModelRegistry, ModelVersionRecord
from src.learning.evaluation.gate import EvaluationGate, GateVerdict, EvaluationBenchmarkResult

__all__ = [
    "ExperienceStore",
    "ExperienceRecord",
    "TrainingDataFactory",
    "TrainingExample",
    "DatasetManifest",
    "ModelRegistry",
    "ModelVersionRecord",
    "EvaluationGate",
    "GateVerdict",
    "EvaluationBenchmarkResult",
]
