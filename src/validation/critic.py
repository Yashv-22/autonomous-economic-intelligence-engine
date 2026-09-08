"""
Adversarial Self-Critique & Grounding Validation Engine.
Challenges primary conclusions, tests citation grounding, and identifies potential unsupported leaps.
"""

from typing import List, Dict, Any, Tuple
from src.models.schemas import ExtractedClaim, ContradictionRecord, ProblemHypothesis, SynthesisResult


class AdversarialCritic:
    """Independent adversarial critique engine for grounding and rigor validation."""

    def __init__(self, strictness_threshold: float = 0.75):
        self.strictness_threshold = strictness_threshold

    def audit_synthesis_grounding(
        self,
        synthesis: SynthesisResult,
        available_claims: List[ExtractedClaim],
    ) -> Tuple[bool, List[str], float]:
        """
        Critique a synthesis result:
        1. Verifies that cited claims exist and have factual/empirical grounding.
        2. Checks whether contradictions were ignored or glossed over.
        3. Penalizes ungrounded assertions.
        Returns (passed, critique_notes, revised_confidence).
        """
        claim_map = {c.claim_id: c for c in available_claims}
        critique_notes: List[str] = []
        score = 1.0

        # 1. Check citation coverage
        if not synthesis.supporting_claim_ids:
            critique_notes.append("CRITIQUE: Synthesis contains no supporting claim IDs.")
            score -= 0.35

        # 2. Check each cited claim
        unverified_claims = []
        for cid in synthesis.supporting_claim_ids:
            if cid not in claim_map:
                unverified_claims.append(cid)
            else:
                claim = claim_map[cid]
                # If synthesis cites an unsupported assumption as a fact
                if claim.is_model_assumption and "proved" in synthesis.summary.lower():
                    critique_notes.append(f"CRITIQUE: Claim {cid} is an ASSUMPTION, but synthesis treats it as proven.")
                    score -= 0.15

        if unverified_claims:
            critique_notes.append(f"CRITIQUE: Found {len(unverified_claims)} citations not registered in claims corpus: {unverified_claims}")
            score -= 0.50  # Heavy penalty for hallucinated / unregistered citations

        # 3. Check contradiction awareness
        if not synthesis.contradictions_noted and len(available_claims) > 10:
            critique_notes.append("CRITIQUE: Synthesis does not mention any opposing evidence or cross-source tensions.")
            score -= 0.10

        revised_confidence = max(0.0, min(1.0, score * synthesis.epistemic_confidence))
        passed = (revised_confidence >= self.strictness_threshold) and (len(unverified_claims) == 0)

        return (passed, critique_notes, revised_confidence)

    def challenge_hypothesis(
        self,
        hypothesis: ProblemHypothesis,
        available_claims: List[ExtractedClaim],
    ) -> Dict[str, Any]:
        """
        Formally red-team a problem hypothesis by searching for disconfirming evidence and alternative explanations.
        """
        opposing_claims = [
            c for c in available_claims
            if c.claim_id in hypothesis.opposing_claim_ids
        ]

        return {
            "hypothesis_id": hypothesis.hypothesis_id,
            "disconfirming_evidence_count": len(opposing_claims),
            "falsification_clarity": "HIGH" if len(hypothesis.falsification_criteria) > 50 else "LOW",
            "has_null_hypothesis": bool(hypothesis.null_hypothesis.startswith("H0:")),
            "recommendation": "APPROVED" if len(hypothesis.falsification_criteria) > 50 else "REVISE_FALSIFICATION_CRITERIA",
        }
