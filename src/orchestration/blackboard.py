"""
Shared Research Blackboard State.
Provides centralized working memory and state tracking across orchestrated agents.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.models.schemas import (
    ResearchObjective,
    SourceSpan,
    ExtractedClaim,
    ContradictionRecord,
    ProblemHypothesis,
    SynthesisResult,
    ResearchGap,
    AuditRecord,
)


class ResearchBlackboard(BaseModel):
    """Working memory blackboard accessible during hierarchical execution."""
    task_id: str
    correlation_id: str
    run_id: Optional[str] = None
    objective: Optional[ResearchObjective] = None
    search_queries: List[str] = Field(default_factory=list)
    spans: List[SourceSpan] = Field(default_factory=list)
    claims: List[ExtractedClaim] = Field(default_factory=list)
    contradictions: List[ContradictionRecord] = Field(default_factory=list)
    hypotheses: List[ProblemHypothesis] = Field(default_factory=list)
    gaps: List[ResearchGap] = Field(default_factory=list)
    synthesis: Optional[SynthesisResult] = None
    merkle_provenance_root: str = ""
    status: str = "INITIALIZED"
    execution_log: List[str] = Field(default_factory=list)
