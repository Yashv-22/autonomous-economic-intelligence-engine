"""
Source Quality & Authority Ranker.
Scores and ranks acquired sources based on institutional authority, primary methodology, evidence density, and recency.
"""

from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from src.internet.providers.base import SearchResultItem


class SourceRanker:
    """Ranks search results and crawled sources to prioritize high-evidentiary-value assets."""

    DOMAIN_AUTHORITY_WEIGHTS: Dict[str, float] = {
        # Academic & Preprints
        "arxiv.org": 0.95,
        "nature.com": 0.95,
        "science.org": 0.95,
        "ieee.org": 0.90,
        "acm.org": 0.90,
        "ssrn.com": 0.88,
        "nber.org": 0.92,
        # Major Research & Consulting Institutions
        "mckinsey.com": 0.88,
        "bcg.com": 0.88,
        "bain.com": 0.86,
        "deloitte.com": 0.85,
        "gartner.com": 0.86,
        "forrester.com": 0.84,
        "hbr.org": 0.88,
        "mit.edu": 0.92,
        "stanford.edu": 0.92,
        # Regulatory & Government
        "sec.gov": 0.95,
        "whitehouse.gov": 0.90,
        "europa.eu": 0.90,
        "oecd.org": 0.90,
        # Tech & Engineering
        "github.com": 0.80,
        "openai.com": 0.85,
        "anthropic.com": 0.85,
        "deepmind.google": 0.90,
        "microsoft.com": 0.82,
        "aws.amazon.com": 0.82,
    }

    @classmethod
    def score_source(cls, item: SearchResultItem, query: str) -> float:
        """Calculate composite quality and relevance score for a search result."""
        domain = item.source_domain.lower()
        base_authority = 0.50

        # Check domain authority table
        for known_domain, weight in cls.DOMAIN_AUTHORITY_WEIGHTS.items():
            if known_domain in domain:
                base_authority = weight
                break

        # Check domain TLD
        if domain.endswith(".edu") or domain.endswith(".gov") or domain.endswith(".org"):
            base_authority = max(base_authority, 0.80)

        # Keyword & query relevance
        query_words = set(query.lower().split())
        title_words = set(item.title.lower().split())
        snippet_words = set(item.snippet.lower().split())

        title_overlap = len(query_words.intersection(title_words)) / max(len(query_words), 1)
        snippet_overlap = len(query_words.intersection(snippet_words)) / max(len(query_words), 1)
        relevance_score = (title_overlap * 0.6) + (snippet_overlap * 0.4)

        # Evidence density heuristic (presence of numbers, percentages, currency, methodology terms)
        evidence_boost = 0.0
        snippet_lower = item.snippet.lower()
        if any(char.isdigit() for char in item.snippet):
            evidence_boost += 0.05
        if "%" in item.snippet or "$" in item.snippet:
            evidence_boost += 0.05
        if any(term in snippet_lower for term in ["methodology", "survey", "empirical", "sample", "dataset", "regression", "model"]):
            evidence_boost += 0.08

        # Primary source boost
        if item.source_type in ["academic", "government"]:
            evidence_boost += 0.05

        composite_score = (base_authority * 0.45) + (relevance_score * 0.35) + (evidence_boost * 0.20)
        return round(min(1.0, composite_score), 4)

    @classmethod
    def rank_sources(cls, items: List[SearchResultItem], query: str) -> List[SearchResultItem]:
        """Rank and return list of SearchResultItem in descending order of evidentiary quality."""
        scored_items = []
        for item in items:
            score = cls.score_source(item, query)
            item.relevance_score = score
            scored_items.append(item)

        scored_items.sort(key=lambda x: x.relevance_score, reverse=True)
        for idx, item in enumerate(scored_items, 1):
            item.rank = idx
        return scored_items
