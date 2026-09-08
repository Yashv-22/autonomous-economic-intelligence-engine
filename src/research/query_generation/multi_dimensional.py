"""
Multi-Dimensional Research Query Generator.
Formulates targeted search questions across 11 distinct analytical dimensions to ensure exhaustive coverage and seek disconfirming evidence.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class ResearchQuery(BaseModel):
    query_text: str
    dimension: str
    priority: float = 1.0
    intent: str
    expected_source_type: str = "web"


class MultiDimensionalQueryGenerator:
    """Generates search vectors covering academic, corporate, technical, economic, organizational, and adversarial angles."""

    DIMENSION_TEMPLATES: Dict[str, List[str]] = {
        "academic": [
            "{topic} empirical research paper pdf",
            "{topic} methodology dataset arxiv",
            "{topic} econometric analysis peer reviewed",
        ],
        "industry": [
            "{topic} McKinsey BCG Bain Gartner report",
            "{topic} benchmark survey findings",
            "{topic} industry transformation case studies",
        ],
        "corporate": [
            "{topic} enterprise 10-K investor presentation",
            "{topic} quarterly earnings commentary adoption",
            "{topic} corporate operating model implementation",
        ],
        "technical": [
            "{topic} system architecture agent mesh orchestration",
            "{topic} straight through routing latency pipeline",
            "{topic} engineering design policy as code",
        ],
        "economic": [
            "{topic} EBITDA return on investment labor economics",
            "{topic} unit economics straight through automation rate alpha",
            "{topic} productivity cost reduction financial variance",
        ],
        "organizational": [
            "{topic} organizational redesign decision rights hierarchy",
            "{topic} workforce restructuring human agent teams",
            "{topic} management control review queue bottlenecks",
        ],
        "negative_evidence": [
            "{topic} transformation failures productivity paradox",
            "{topic} criticism implementation bottlenecks earnings miss",
            "{topic} why enterprise AI fails review fatigue risks",
        ],
        "historical": [
            "{topic} lessons from prior automation IT transformations",
            "{topic} historical technology transitions productivity lag",
        ],
        "competitive": [
            "{topic} comparative approaches across finance healthcare tech",
            "{topic} market leaders vs laggards execution gap",
        ],
        "regulatory": [
            "{topic} EU AI Act compliance governance accountability",
            "{topic} legal risk auditability supervisory oversight",
        ],
        "expert_independent": [
            "{topic} HBR MIT Sloan independent analysis",
            "{topic} expert critique research findings",
        ],
    }

    @classmethod
    def generate_queries(
        cls,
        topic: str,
        dimensions: Optional[List[str]] = None,
        max_queries: int = 15,
    ) -> List[ResearchQuery]:
        """Generate a prioritized list of research queries spanning specified dimensions."""
        target_dimensions = dimensions or list(cls.DIMENSION_TEMPLATES.keys())
        queries: List[ResearchQuery] = []

        for dim in target_dimensions:
            templates = cls.DIMENSION_TEMPLATES.get(dim.lower(), [])
            for tmpl in templates:
                q_text = tmpl.format(topic=topic)
                # Prioritize negative evidence, economics, academic, and industry
                priority = 1.0
                if dim.lower() in ["negative_evidence", "economic", "academic"]:
                    priority = 1.2
                elif dim.lower() in ["industry", "organizational"]:
                    priority = 1.1

                queries.append(
                    ResearchQuery(
                        query_text=q_text,
                        dimension=dim,
                        priority=priority,
                        intent=f"Investigate {dim} dimension for topic: {topic}",
                        expected_source_type="academic" if dim == "academic" else "web",
                    )
                )

        # Sort by priority descending
        queries.sort(key=lambda q: q.priority, reverse=True)
        return queries[:max_queries]
