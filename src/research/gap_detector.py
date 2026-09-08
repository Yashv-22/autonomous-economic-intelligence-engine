"""
Autonomous Research Gap Detection Engine.
Identifies evidentiary deficits, low-confidence assertions, and under-explored parameters
using the deterministic 9-class EpistemicUncertaintyEngine.
"""

from typing import List, Optional, Any
from src.models.schemas import ExtractedClaim, ResearchGap, ResearchObjective, EvidenceGrade, ContradictionRecord
from src.research.uncertainty import EpistemicUncertaintyEngine, UncertaintyBreakdown, EvidenceGap


class ResearchGapDetector:
    """Detects missing variables and evidence voids in knowledge base."""

    @classmethod
    def detect_gaps(
        cls,
        objective: ResearchObjective,
        claims: List[ExtractedClaim],
        contradictions: Optional[List[ContradictionRecord]] = None,
        previous_resolved_gaps: Optional[List[str]] = None,
    ) -> List[str]:
        """Analyze claim corpus against objective to isolate missing variables and return list of gap queries."""
        breakdown = cls.detect_structured_gaps(objective, claims, contradictions, previous_resolved_gaps)
        return [gap.actionable_query for gap in breakdown.active_gaps]

    @classmethod
    def detect_structured_gaps(
        cls,
        objective: ResearchObjective,
        claims: List[ExtractedClaim],
        contradictions: Optional[List[ContradictionRecord]] = None,
        previous_resolved_gaps: Optional[List[str]] = None,
    ) -> UncertaintyBreakdown:
        """Deterministically map evidence gaps and compute the full uncertainty breakdown."""
        return EpistemicUncertaintyEngine.evaluate_uncertainty(
            topic=objective.topic,
            claims=claims,
            contradictions=contradictions,
            previous_resolved_gaps=previous_resolved_gaps,
        )
