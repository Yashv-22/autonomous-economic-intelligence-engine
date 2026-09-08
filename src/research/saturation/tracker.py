"""
Research Saturation Tracker.
Evaluates marginal information gain across research cycles to recognize diminishing returns and prevent redundant querying.
"""

from typing import List, Dict, Any, Tuple
from pydantic import BaseModel


class SaturationMetrics(BaseModel):
    new_claims_ratio: float
    new_entities_ratio: float
    source_redundancy_rate: float
    gap_closure_rate: float
    marginal_gain_score: float
    is_saturated: bool
    saturation_reason: str = ""


class ResearchSaturationTracker:
    """Calculates diminishing returns and detects when the research frontier is saturated."""

    def __init__(self, min_marginal_gain_threshold: float = 0.10):
        self.threshold = min_marginal_gain_threshold

    def evaluate_saturation(
        self,
        total_sources_seen: int,
        new_sources_acquired: int,
        total_claims_before: int,
        new_claims_extracted: int,
        total_entities_before: int,
        new_entities_found: int,
        open_gaps_count: int,
        resolved_gaps_count: int,
    ) -> SaturationMetrics:
        """Calculate composite marginal gain and determine if research saturation is reached."""
        # 1. New claims per source
        claims_gain = (new_claims_extracted / max(new_sources_acquired, 1)) if new_sources_acquired > 0 else 0.0
        normalized_claims_gain = min(1.0, claims_gain / 10.0)

        # 2. Entity novelty
        entity_novelty = (new_entities_found / max(total_entities_before + 1, 1))
        normalized_entity_novelty = min(1.0, entity_novelty * 2.0)

        # 3. Source redundancy
        redundancy_rate = 1.0 - (new_sources_acquired / max(total_sources_seen, 1))

        # 4. Gap resolution
        total_gaps = open_gaps_count + resolved_gaps_count
        gap_closure = (resolved_gaps_count / max(total_gaps, 1)) if total_gaps > 0 else 0.5

        # Composite marginal information gain
        marginal_gain = (
            (normalized_claims_gain * 0.40)
            + (normalized_entity_novelty * 0.35)
            + ((1.0 - redundancy_rate) * 0.15)
            + (gap_closure * 0.10)
        )

        is_saturated = False
        reason = "Information gain active; expanding research frontier."

        if total_sources_seen >= 10 and marginal_gain < self.threshold:
            is_saturated = True
            reason = (
                f"RESEARCH SATURATION REACHED: Marginal information gain ({marginal_gain:.2f}) "
                f"fell below threshold ({self.threshold:.2f}). High source redundancy ({redundancy_rate:.1%})."
            )

        return SaturationMetrics(
            new_claims_ratio=round(normalized_claims_gain, 4),
            new_entities_ratio=round(normalized_entity_novelty, 4),
            source_redundancy_rate=round(redundancy_rate, 4),
            gap_closure_rate=round(gap_closure, 4),
            marginal_gain_score=round(marginal_gain, 4),
            is_saturated=is_saturated,
            saturation_reason=reason,
        )
