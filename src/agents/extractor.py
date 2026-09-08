"""
Claim Extraction Agent.
Extracts structured claims, assigns epistemic grades, and anchors source spans.
"""

from typing import List
from src.agents.base import BaseAgent, AgentContext
from src.models.schemas import ToolPermission, SourceSpan, ExtractedClaim
from src.extraction.claim_extractor import ClaimExtractor


class ClaimExtractorAgent(BaseAgent):
    """Specialized agent for extracting structured claims and metrics from source spans."""

    name: str = "ClaimExtractorAgent"
    role: str = "Claim Extraction & Epistemic Classifier"
    description: str = "Transforms raw text spans into atomic claims with epistemic grades and metrics."
    allowed_tools: List[str] = []
    permission_level: ToolPermission = ToolPermission.READ_ONLY

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.extractor = ClaimExtractor()

    def run(self, context: AgentContext, spans: List[SourceSpan], **kwargs) -> List[ExtractedClaim]:
        """Extract all claims from spans."""
        claims = self.extractor.extract_claims_from_spans(spans)
        return claims
