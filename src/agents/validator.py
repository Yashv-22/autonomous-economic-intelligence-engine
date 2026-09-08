"""
Validation & Contradiction Detection Agent.
Detects cross-source tensions, formulates falsifiable problem hypotheses, and performs adversarial critique.
"""

from typing import List, Tuple
from src.agents.base import BaseAgent, AgentContext
from src.models.schemas import (
    ToolPermission,
    ExtractedClaim,
    ContradictionRecord,
    ProblemHypothesis,
)
from src.validation.contradiction import ContradictionDetector
from src.validation.hypothesis import HypothesisGenerator
from src.validation.critic import AdversarialCritic


class ValidationCriticAgent(BaseAgent):
    """Specialized agent for analytical tension detection and hypothesis formulation."""

    name: str = "ValidationCriticAgent"
    role: str = "Validation & Adversarial Critic"
    description: str = "Detects contradictions, formulates falsifiable hypotheses, and red-teams conclusions."
    allowed_tools: List[str] = []
    permission_level: ToolPermission = ToolPermission.READ_ONLY

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.detector = ContradictionDetector()
        self.hypothesis_gen = HypothesisGenerator()
        self.critic = AdversarialCritic()

    def run(
        self,
        context: AgentContext,
        claims: List[ExtractedClaim],
        **kwargs
    ) -> Tuple[List[ContradictionRecord], List[ProblemHypothesis]]:
        """Run contradiction detection and problem hypothesis formulation."""
        contradictions = self.detector.detect_contradictions(claims)
        hypotheses = self.hypothesis_gen.generate_hypotheses(claims, contradictions)
        return contradictions, hypotheses
