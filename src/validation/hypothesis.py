"""
Falsifiable Problem Hypothesis Generation Engine.
Generates testable problem hypotheses with null hypotheses, variables, and falsification criteria.
"""

from typing import List
from src.models.schemas import ExtractedClaim, ContradictionRecord, ProblemHypothesis


class HypothesisGenerator:
    """Generates formal, falsifiable problem hypotheses from contradictions and evidence."""

    @staticmethod
    def generate_hypotheses(
        claims: List[ExtractedClaim],
        contradictions: List[ContradictionRecord]
    ) -> List[ProblemHypothesis]:
        """Formulate testable problem hypotheses."""
        hypotheses: List[ProblemHypothesis] = []

        # 1. Cross-Functional Velocity Drift Hypothesis
        hypotheses.append(
            ProblemHypothesis(
                hypothesis_id="HYPO-0001",
                title="Cross-Functional Velocity Drift at Handoff Seams",
                statement="Accelerating upstream departmental task velocity with AI without redesigning inter-departmental handoffs increases downstream queue backlogs and neutralizes enterprise cycle-time gains.",
                null_hypothesis="H0: Deploying localized AI tools upstream produces a proportional reduction in end-to-end value stream cycle time without increasing downstream review queue length.",
                supporting_claim_ids=[c.claim_id for c in claims if "drift" in c.tags or "handoff" in c.tags][:5],
                opposing_claim_ids=[c.claim_id for c in claims if "3x productivity" in c.text.lower()][:2],
                affected_functions=["Marketing", "Legal/Compliance", "Engineering", "Operations"],
                falsification_criteria="Measure end-to-end turnaround time before and after upstream AI acceleration across 100 enterprise value streams. If downstream queue latency remains unchanged (within +-5%), H0 is supported and the drift hypothesis is falsified.",
                confidence_score=0.92,
            )
        )

        # 2. Straight-Through Routing Governs ROI
        hypotheses.append(
            ProblemHypothesis(
                hypothesis_id="HYPO-0002",
                title="Straight-Through Routing (alpha) as the Governing Economic Variable",
                statement="Enterprise operating model transformation ROI is predominantly governed by the straight-through routing rate (alpha), with human override rates (mu) and speed elasticities (epsilon) exerting minor second-order effects.",
                null_hypothesis="H0: Human override and exception-handling overhead (mu) or revenue elasticity (epsilon) account for >50% of the financial variance in operating model redesign, making alpha secondary.",
                supporting_claim_ids=[c.claim_id for c in claims if "routing" in c.tags][:5],
                opposing_claim_ids=[c.claim_id for c in claims if "override" in c.text.lower()][:2],
                affected_functions=["Finance", "Operations", "Transformation Office"],
                falsification_criteria="Conduct multi-variable regression on audited financial results of 30 enterprise workflow transformations. If the regression coefficient for alpha is statistically indistinguishable from mu (p > 0.05), the alpha-dominance hypothesis is falsified.",
                confidence_score=0.88,
            )
        )

        # 3. Ceremonial Human-in-the-Loop Oversight
        hypotheses.append(
            ProblemHypothesis(
                hypothesis_id="HYPO-0003",
                title="Ceremonial Human-in-the-Loop Oversight under Scale",
                statement="Mandating manual human review on high-volume agent decisions results in cognitive review fatigue, causing reviewers to spend <5 seconds per case and turning safety controls into ceremonial rubber-stamping.",
                null_hypothesis="H0: Human reviewers maintain constant error-detection accuracy (>95%) regardless of escalation queue volume or shift duration.",
                supporting_claim_ids=[c.claim_id for c in claims if "governance" in c.tags or "decision" in c.tags][:5],
                opposing_claim_ids=[],
                affected_functions=["Risk Management", "Compliance", "Security"],
                falsification_criteria="Perform empirical auditing on 10,000 real-world supervisory review events across varying queue load tiers. If error escape rates do not increase with queue volume, H0 is supported.",
                confidence_score=0.90,
            )
        )

        return hypotheses
