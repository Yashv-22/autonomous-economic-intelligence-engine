"""
Epistemic Claim Classifier & Evidence Grading Engine.
Classifies research claims into FACT, EVIDENCE, INFERENCE, HYPOTHESIS, ASSUMPTION, RECOMMENDATION.
"""

import re
from typing import Tuple
from src.models.schemas import EvidenceGrade


class EvidenceClassifier:
    """Classifies extracted text claims into epistemic evidence tiers."""

    # Epistemic marker heuristics
    FACT_PATTERNS = [
        r"\b(ISO|SOC\s?2|HIPAA|GDPR|protocol|specification|RFC|standard|law|statute)\b",
        r"\b(SHA-256|PostgreSQL|API|JSON|REST|GraphQL|OAuth|deterministic)\b",
    ]

    EVIDENCE_PATTERNS = [
        r"\b(survey|study|findings|reported|measured|observed|empirical|data shows|percent of|% of)\b",
        r"\b(PwC|McKinsey|BCG|Deloitte|Gartner|Forrester|Stanford|Accenture|KPMG|EY)\b",
        r"\b\d+(\.\d+)?%\b",  # Matches percentages (e.g. 88%, 74%)
    ]

    ASSUMPTION_PATTERNS = [
        r"\b(model parameter|assumed|base case|parameters model|parametric|worked illustration|assumes)\b",
        r"\b(sensitivity analysis|constant volume|illustrative annual|reconciles to the dollar)\b",
    ]

    RECOMMENDATION_PATTERNS = [
        r"\b(should|must|requires|recommends|ought to|best practice|directive|mandate)\b",
        r"\b(redesign precedes|governance is designed in|scope is one or two)\b",
    ]

    HYPOTHESIS_PATTERNS = [
        r"\b(hypothesized|hypothesis|potential|may produce|could lead to|predicted|tentative)\b",
        r"\b(untested|yet to be proven|speculative|further research)\b",
    ]

    INFERENCE_PATTERNS = [
        r"\b(it follows that|therefore|indicates that|suggests that|consequence is|points to)\b",
        r"\b(implies|derived from|explains how|corroborating)\b",
    ]

    @classmethod
    def classify(cls, text: str, section: str = "") -> Tuple[EvidenceGrade, bool, float]:
        """
        Classify text span and return (EvidenceGrade, is_model_assumption, confidence).
        """
        text_lower = text.lower()
        section_lower = section.lower()

        # Check for explicit model assumptions
        if any(re.search(p, text_lower) for p in cls.ASSUMPTION_PATTERNS) or "economic model" in section_lower or "sensitivity" in section_lower:
            return EvidenceGrade.ASSUMPTION, True, 0.95

        # Check for prescriptive recommendations
        if any(re.search(p, text_lower) for p in cls.RECOMMENDATION_PATTERNS) or "recommend" in section_lower:
            return EvidenceGrade.RECOMMENDATION, False, 0.90

        # Check for empirical survey/case evidence
        if any(re.search(p, text_lower) for p in cls.EVIDENCE_PATTERNS):
            return EvidenceGrade.EVIDENCE, False, 0.92

        # Check for verified technical facts / standards
        if any(re.search(p, text_lower) for p in cls.FACT_PATTERNS):
            return EvidenceGrade.FACT, False, 0.90

        # Check for formal hypotheses
        if any(re.search(p, text_lower) for p in cls.HYPOTHESIS_PATTERNS) or "hypothesis" in section_lower:
            return EvidenceGrade.HYPOTHESIS, False, 0.88

        # Check for analytical inferences
        if any(re.search(p, text_lower) for p in cls.INFERENCE_PATTERNS):
            return EvidenceGrade.INFERENCE, False, 0.85

        # Default fallback
        return EvidenceGrade.INFERENCE, False, 0.70
