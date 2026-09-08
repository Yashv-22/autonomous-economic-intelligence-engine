"""
Experience Memory Store.
Persists operational traces, tool usage, search paths, user corrections, and feedback to enable experience learning.
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.core.identifiers import generate_prefixed_id
from src.core.logging import logger


class ExperienceRecord(BaseModel):
    experience_id: str
    task_type: str  # research_search, extraction, contradiction_detection, synthesis, user_correction
    input_context: Dict[str, Any]
    action_taken: Dict[str, Any]
    outcome_result: Dict[str, Any]
    feedback_score: float = 1.0  # 1.0 = success, -1.0 = failure, 0.0 = neutral
    evaluator_or_user_notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ExperienceStore:
    """Stores operational experience logs and feedback for offline learning."""

    def __init__(self, base_dir: str = "data/experience"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.log_file = os.path.join(self.base_dir, "experiences.jsonl")

    def record_experience(
        self,
        task_type: str,
        input_context: Dict[str, Any],
        action_taken: Dict[str, Any],
        outcome_result: Dict[str, Any],
        feedback_score: float = 1.0,
        notes: Optional[str] = None,
    ) -> ExperienceRecord:
        """Append an operational trace record to experience log."""
        record = ExperienceRecord(
            experience_id=generate_prefixed_id("EXP"),
            task_type=task_type,
            input_context=input_context,
            action_taken=action_taken,
            outcome_result=outcome_result,
            feedback_score=feedback_score,
            evaluator_or_user_notes=notes,
        )

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.dict()) + "\n")

        logger.info(f"ExperienceStore: Recorded {task_type} trace [{record.experience_id}] (Score: {feedback_score})")
        return record

    def record_user_correction(self, original_claim_or_finding: str, corrected_text: str, reason: str) -> ExperienceRecord:
        """Record explicit user feedback / correction as high-value training signal."""
        return self.record_experience(
            task_type="user_correction",
            input_context={"original": original_claim_or_finding},
            action_taken={"correction_applied": corrected_text},
            outcome_result={"verified_truth": corrected_text},
            feedback_score=1.0,
            notes=reason,
        )

    def get_experiences(self, task_type: Optional[str] = None, limit: int = 100) -> List[ExperienceRecord]:
        """Retrieve recorded experience records."""
        if not os.path.exists(self.log_file):
            return []

        records = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = ExperienceRecord(**json.loads(line))
                    if not task_type or rec.task_type == task_type:
                        records.append(rec)
        return records[-limit:]
