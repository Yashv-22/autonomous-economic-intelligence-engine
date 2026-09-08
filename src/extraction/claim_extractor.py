"""
Structured Claim Extraction Engine.
Extracts normalized research claims with source provenance, institutions, metrics, polarity, and epistemic tags from raw document spans.
"""

import re
from typing import List, Optional, Tuple
from src.models.schemas import SourceSpan, ExtractedClaim, EvidenceGrade
from src.extraction.classifier import EvidenceClassifier


class ClaimExtractor:
    """Extracts structured research claims and figures from document spans."""

    INSTITUTION_KEYWORDS = [
        "McKinsey",
        "Boston Consulting Group",
        "BCG",
        "Bain & Company",
        "Bain",
        "Deloitte",
        "PwC",
        "Gartner",
        "Forrester",
        "Accenture",
        "KPMG",
        "EY",
        "IBM",
        "Stanford HAI",
        "World Economic Forum",
        "WEF",
        "MIT SMR",
        "Harvard Data Science Review",
        "HBR",
        "Anthropic",
        "Microsoft",
        "Google",
    ]

    TOPIC_MAPPINGS = {
        "drift": "Cross-Functional Drift",
        "handoff": "Handoff Bottlenecks",
        "swivel": "Swivel-Chair Overhead",
        "routing": "Straight-Through Routing (alpha)",
        "automation": "Workflow Automation",
        "decision": "Decision Rights Architecture",
        "governance": "Policy & Governance",
        "ebitda": "Economic & EBITDA Returns",
        "earnings": "Economic & EBITDA Returns",
        "paradox": "AI Productivity Paradox",
        "readiness": "AI-Readiness Debt",
        "agent": "Agentic Architecture",
        "identity": "Non-Human Identity (NHI)",
        "adoption": "Enterprise AI Adoption",
    }

    def __init__(self):
        self.claim_counter = 0

    def extract_claims_from_spans(self, spans: List[SourceSpan]) -> List[ExtractedClaim]:
        """Extract structured claims from a list of SourceSpans."""
        extracted_claims: List[ExtractedClaim] = []

        for span in spans:
            # Skip reference bibliography citations
            if "References" in span.page_or_section or "Reference Library" in span.text:
                continue

            claims = self._extract_from_single_span(span)
            extracted_claims.extend(claims)

        return extracted_claims

    def _extract_from_single_span(self, span: SourceSpan) -> List[ExtractedClaim]:
        """Process an individual text span and extract salient claims."""
        results: List[ExtractedClaim] = []
        text = span.text.strip()

        # Split text into candidate sentences
        raw_sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", text) if len(s.strip()) > 25]
        if not raw_sentences:
            raw_sentences = [text]

        atomic_sentences = []
        for s in raw_sentences:
            # Decompose compound comparative sentences (e.g., "while X, Y") into atomic assertions
            if "while " in s.lower() and ("," in s or ";" in s):
                parts = re.split(r",\s*(?:while|over|whereas|however|but)\s*", s, flags=re.IGNORECASE)
                for part in parts:
                    clean_part = part.strip()
                    if clean_part.lower().startswith("while "):
                        clean_part = clean_part[6:].strip()
                    if len(clean_part) > 25:
                        atomic_sentences.append(clean_part)
            else:
                atomic_sentences.append(s)

        for sentence in atomic_sentences:
            if not self._is_substantive_claim(sentence):
                continue

            self.claim_counter += 1
            claim_id = f"CLAIM-{self.claim_counter:04d}"

            institution = self._detect_institution(sentence)
            metric = self._detect_metric(sentence)
            grade, is_assumption, confidence = EvidenceClassifier.classify(sentence, span.page_or_section)
            topic, tags = self._detect_topic_and_tags(sentence)
            polarity = self._detect_polarity(sentence)

            results.append(
                ExtractedClaim(
                    claim_id=claim_id,
                    text=sentence,
                    entity_or_topic=topic,
                    evidence_grade=grade,
                    institution=institution,
                    quantitative_metric=metric,
                    is_model_assumption=is_assumption,
                    source_span=span,
                    confidence_score=confidence,
                    tags=tags,
                    polarity=polarity,
                )
            )

        return results

    def _is_substantive_claim(self, sentence: str) -> bool:
        """Filter out boilerplate, table headers, or non-informative fragments."""
        lower = sentence.lower()
        if len(sentence) < 30:
            return False
        # Filter table header rows
        if "institution | core framework" in lower or "operational mechanism | headline metric" in lower:
            return False
        if lower.startswith("page ") or lower.startswith("table ") or lower.startswith("figure "):
            return False
        if "confidential" in lower and len(sentence) < 60:
            return False
        return any(
            term in lower
            for term in [
                "is", "are", "shows", "reports", "requires", "model", "found", "causes",
                "rate", "cost", "drift", "value", "percent", "%", "gain", "ebitda",
                "adoption", "bottleneck", "scale", "increase", "reduce", "governance"
            ]
        )

    def _detect_institution(self, text: str) -> Optional[str]:
        for inst in self.INSTITUTION_KEYWORDS:
            if re.search(rf"\b{re.escape(inst)}\b", text, re.IGNORECASE):
                return inst
        return None

    def _detect_metric(self, text: str) -> Optional[str]:
        metric_pattern = r"(\b\d+(?:\.\d+)?%|\$\d+(?:[,\.]\d+)?(?:\s*(?:m|b|k|million|billion|trillion))?|\b\d+x|\b\d+–\d+x|\b\d+-\d+x)"
        match = re.search(metric_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _detect_topic_and_tags(self, text: str) -> Tuple[str, List[str]]:
        lower = text.lower()
        tags = []
        primary_topic = "Organizational Transformation"

        for keyword, topic_name in self.TOPIC_MAPPINGS.items():
            if keyword in lower:
                tags.append(keyword)
                if primary_topic == "Organizational Transformation":
                    primary_topic = topic_name

        if not tags:
            tags.append("general")

        return primary_topic, tags

    def _detect_polarity(self, text: str) -> str:
        """Detect whether the claim indicates positive progress, friction/risk, or neutral fact."""
        lower = text.lower()
        negative_words = ["drift", "bottleneck", "backlog", "fail", "fatigue", "lack", "no material impact", "collapse", "risk", "unsupported", "negligible"]
        positive_words = ["gain", "uplift", "accelerate", "improve", "roi", "savings", "scale", "productive", "success"]

        has_neg = any(w in lower for w in negative_words)
        has_pos = any(w in lower for w in positive_words)

        if has_neg and not has_pos:
            return "NEGATIVE"
        if has_pos and not has_neg:
            return "POSITIVE"
        return "NEUTRAL"
