"""
Opportunity Discovery & SaaS / AI Solution Generation Package.
"""

from src.opportunity.schemas import MarketProblemRecord, SaaSSolutionOpportunity, OpportunityMatrixResponse
from src.opportunity.engine import OpportunityDiscoveryEngine

__all__ = [
    "MarketProblemRecord",
    "SaaSSolutionOpportunity",
    "OpportunityMatrixResponse",
    "OpportunityDiscoveryEngine",
]
