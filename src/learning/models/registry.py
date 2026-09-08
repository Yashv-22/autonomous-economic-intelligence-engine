"""
Model Registry & Version Management.
Tracks model versions, lineage to training datasets, evaluation benchmarks, rollback pointers, and deployment stages.
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.core.identifiers import generate_prefixed_id
from src.core.logging import logger


class ModelVersionRecord(BaseModel):
    model_version_id: str  # e.g. model-v001, model-v002
    base_model_name: str  # e.g. gemini-1.5-pro, llama-3-70b-instruct, fine-tuned-operating-model-v1
    dataset_version: str  # dataset manifest version
    training_run_id: str
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    evaluation_scores: Dict[str, float] = Field(default_factory=dict)
    known_weaknesses: List[str] = Field(default_factory=list)
    deployment_status: str = "CANDIDATE"  # CANDIDATE, SHADOW, PRODUCTION, ARCHIVED, REJECTED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    promoted_at: Optional[str] = None
    previous_version_id: Optional[str] = None


class ModelRegistry:
    """Manages versioned model artifacts, metadata, and rollback state."""

    def __init__(self, registry_file: str = "data/models/model_registry.json"):
        self.registry_file = registry_file
        os.makedirs(os.path.dirname(os.path.abspath(self.registry_file)), exist_ok=True)
        self.models: Dict[str, ModelVersionRecord] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.models = {k: ModelVersionRecord(**v) for k, v in data.items()}
            except Exception as e:
                logger.warning(f"Error loading model registry: {e}")

    def _save(self):
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump({k: v.dict() for k, v in self.models.items()}, f, indent=2)

    def register_model(
        self,
        version: str,
        training_dataset_id: str,
        lineage_manifest_path: str = "",
        hyperparameters: Optional[Dict[str, Any]] = None,
        evaluation_score: float = 0.90,
        base_model_name: str = "operating-model-base-v1",
    ) -> ModelVersionRecord:
        """Convenience registration method."""
        rec = ModelVersionRecord(
            model_version_id=version,
            base_model_name=base_model_name,
            dataset_version=training_dataset_id,
            training_run_id=generate_prefixed_id("RUN"),
            hyperparameters=hyperparameters or {},
            evaluation_scores={"overall_score": evaluation_score},
            deployment_status="CANDIDATE",
        )
        self.models[version] = rec
        self._save()
        logger.info(f"ModelRegistry: Registered model '{version}'")
        return rec

    def register_model_version(
        self,
        base_model: str,
        dataset_version: str,
        training_run_id: str,
        evaluation_scores: Dict[str, float],
        hyperparameters: Optional[Dict[str, Any]] = None,
        weaknesses: Optional[List[str]] = None,
    ) -> ModelVersionRecord:
        """Register a new candidate model version."""
        version_num = len(self.models) + 1
        model_id = f"model-v{version_num:03d}"
        
        # Determine previous production version for rollback pointer
        current_prod = self.get_production_model()
        prev_id = current_prod.model_version_id if current_prod else None

        record = ModelVersionRecord(
            model_version_id=model_id,
            base_model_name=base_model,
            dataset_version=dataset_version,
            training_run_id=training_run_id,
            hyperparameters=hyperparameters or {"epochs": 3, "lr": 2e-5, "lora_r": 16},
            evaluation_scores=evaluation_scores,
            known_weaknesses=weaknesses or [],
            deployment_status="CANDIDATE",
            previous_version_id=prev_id,
        )

        self.models[model_id] = record
        self._save()
        logger.info(f"ModelRegistry: Registered new candidate '{model_id}' (Lineage: {dataset_version})")
        return record

    def promote_to_production(self, model_version_id: str) -> Optional[ModelVersionRecord]:
        """Promotes a candidate/shadow model to production and archives or shadows previous production models."""
        if model_version_id not in self.models:
            logger.error(f"Cannot promote unknown model '{model_version_id}'")
            return None

        for k, v in self.models.items():
            if v.deployment_status == "PRODUCTION":
                v.deployment_status = "SHADOW"

        target = self.models[model_version_id]
        target.deployment_status = "PRODUCTION"
        target.promoted_at = datetime.now(timezone.utc).isoformat()
        self._save()
        logger.info(f"ModelRegistry: Model '{model_version_id}' promoted to PRODUCTION.")
        return target

    promote_model_to_production = promote_to_production


    def rollback(self) -> Optional[ModelVersionRecord]:
        """Rollback production to the previous stable model version."""
        current = self.get_production_model()
        if not current or not current.previous_version_id:
            logger.warning("Rollback unavailable: No prior production version found.")
            return None

        prev_id = current.previous_version_id
        if prev_id in self.models:
            current.deployment_status = "ARCHIVED"
            self.models[prev_id].deployment_status = "PRODUCTION"
            self._save()
            logger.info(f"ModelRegistry: Rolled back from {current.model_version_id} to {prev_id}")
            return self.models[prev_id]
        return None

    def get_production_model(self) -> Optional[ModelVersionRecord]:
        """Retrieve current production model."""
        for rec in self.models.values():
            if rec.deployment_status == "PRODUCTION":
                return rec
        return None

    def list_models(self) -> List[ModelVersionRecord]:
        """List all registered models."""
        return list(self.models.values())
