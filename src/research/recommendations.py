"""
Contextual Search Recommendation & Research Director Integration.
Authoritative next-step decision layer that bridges Research History,
Epistemic Uncertainty, Evidence Gaps, and the Research Director's multi-factor priority formula.
"""

import json
import re
from typing import List, Dict, Any, Optional
from src.core.logging import logger
from src.research.director import ResearchDirectorEngine, NextBestResearchInvestigation
from src.research.uncertainty import EpistemicUncertaintyEngine, UncertaintyBreakdown


class SearchRecommendationEngine:
    """
    Intelligent recommendation engine driven by the Research Director.
    Calculates the single most valuable next investigation to perform and provides
    structured follow-up vectors across commercial, architectural, and empirical dimensions.
    """

    CATEGORIES = {
        "CONTRADICTION_PROBE": "Contradiction Probe",
        "HYPOTHESIS_TEST": "Hypothesis Test",
        "COMMERCIAL_MOAT": "Unit Economics & Moat",
        "ARCHITECTURE_BOTTLENECK": "Technical Architecture",
        "REGULATORY_COMPLIANCE": "Regulatory & Risk",
    }

    @classmethod
    def get_director_investigations(
        cls,
        topic: str,
        claims: Optional[List[Any]] = None,
        contradictions: Optional[List[Any]] = None,
        opportunities: Optional[List[Any]] = None,
        resolved_queries: Optional[List[str]] = None,
        history_topics: Optional[List[str]] = None,
    ) -> List[NextBestResearchInvestigation]:
        """Fetch the authoritative ranked investigations directly from the Research Director."""
        return ResearchDirectorEngine.evaluate_next_best_research(
            topic=topic,
            claims=claims or [],
            contradictions=contradictions or [],
            opportunities=opportunities or [],
            resolved_investigation_queries=resolved_queries or [],
            history_topics=history_topics or [],
        )

    @classmethod
    def generate_next_searches(
        cls,
        topic: str,
        query: Optional[str] = None,
        claims: Optional[List[Any]] = None,
        contradictions: Optional[List[Any]] = None,
        hypotheses: Optional[List[Any]] = None,
        opportunities: Optional[List[Any]] = None,
        use_llm: bool = False,  # Deterministic mathematical calculation is primary per user directive
        resolved_queries: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate structured next-search recommendations driven by the Research Director.
        Integrates multi-factor priority scoring, expected information gain, and uncertainty mapping.
        """
        clean_topic = (topic or "").strip() or "Enterprise AI Operating Model Redesign"
        clean_query = (query or "").strip() or clean_topic

        # Fetch investigations from authoritative Research Director
        director_investigations = cls.get_director_investigations(
            topic=clean_topic,
            claims=claims or [],
            contradictions=contradictions or [],
            opportunities=opportunities or [],
            resolved_queries=resolved_queries or [],
        )

        suggestions: List[Dict[str, Any]] = []

        # Map director investigations into structured suggestion dictionaries
        for idx, inv in enumerate(director_investigations[:5]):
            cat_key = "COMMERCIAL_MOAT"
            if "CONTRADICTION" in inv.gap_class or "CONFLICTING" in inv.gap_class:
                cat_key = "CONTRADICTION_PROBE"
            elif "TECH" in inv.gap_class or "FEASIBILITY" in inv.gap_class:
                cat_key = "ARCHITECTURE_BOTTLENECK"
            elif "PRIMARY" in inv.gap_class or "SAMPLE" in inv.gap_class:
                cat_key = "HYPOTHESIS_TEST"
            elif "BUYER" in inv.gap_class or "ECON" in inv.gap_class:
                cat_key = "COMMERCIAL_MOAT"

            suggestions.append({
                "id": f"dir-sugg-{idx + 1}",
                "title": inv.question,
                "query": inv.actionable_query,
                "category": cat_key,
                "category_label": cls.CATEGORIES.get(cat_key, "Strategic Inquiry"),
                "rationale": inv.why_it_matters,
                "priority_rank": inv.priority_rank,
                "priority_score": inv.priority_score,
                "expected_information_gain": inv.expected_information_gain,
                "current_uncertainty": inv.current_uncertainty,
                "current_uncertainty_label": inv.current_uncertainty_label,
                "economic_relevance": inv.economic_relevance,
                "actionability": inv.actionability,
                "research_cost": inv.research_cost,
                "score_method": inv.score_method,
                "evidence_basis": inv.evidence_basis,
                "confidence": inv.confidence,
                "is_director_top_mandate": (idx == 0),
                "recommended_depth": 2 if inv.research_cost <= 1.2 else 3,
                "recommended_budget": 5 if inv.research_cost <= 1.2 else 10,
            })

        return suggestions[:4]
