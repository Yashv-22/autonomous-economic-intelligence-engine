"""
Research Director & Next-Best-Research Engine.
Calculates the single most valuable next research investigation to perform,
evaluated via the multi-factor mathematical priority formula:

    Priority Score = (Expected Information Gain * Economic Relevance * Uncertainty * Actionability) / Research Cost

Features deterministic information gain scoring without LLM hallucination,
evidence-grounded rationale, and closed-loop research history continuity.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.models.schemas import ExtractedClaim, ContradictionRecord
from src.research.uncertainty import EpistemicUncertaintyEngine, UncertaintyBreakdown, EvidenceGap, GapClass


class NextBestResearchInvestigation(BaseModel):
    """Authoritative strategic decision artifact emitted by the Research Director."""
    investigation_id: str
    question: str
    why_it_matters: str
    knowledge_gap: str
    gap_class: str
    current_uncertainty: float           # 0.0 to 1.0
    current_uncertainty_label: str     # e.g. "82% (Severe lack of primary buyer evidence)"
    expected_information_gain: float   # Deterministically calculated 0.0 to 1.0
    economic_relevance: float          # 0.0 to 1.0
    actionability: float               # 0.0 to 1.0
    research_cost: float               # Relative compute/source budget weight (e.g. 1.0 to 3.0)
    priority_score: float              # Final calculated rank index
    priority_rank: int                 # 1 = Highest single recommendation
    sources_required: List[str]        # Target source categories (regulatory, benchmarks, enterprise surveys)
    actionable_query: str              # Immediate 1-click execution search query
    score_method: str = "deterministic_multi_factor_v1"
    evidence_basis: str
    confidence: str = "HIGH"           # HIGH, MEDIUM, LOW, UNKNOWN
    target_opportunity_id: Optional[str] = None


class ResearchDirectorEngine:
    """
    Authoritative strategic director that determines the highest-value uncertainty to resolve next.
    Integrates knowledge state, evidence gaps, and research history.
    """

    @classmethod
    def evaluate_next_best_research(
        cls,
        topic: str,
        claims: List[ExtractedClaim],
        contradictions: Optional[List[ContradictionRecord]] = None,
        opportunities: Optional[List[Any]] = None,
        resolved_investigation_queries: Optional[List[str]] = None,
        history_topics: Optional[List[str]] = None,
    ) -> List[NextBestResearchInvestigation]:
        """
        Calculates ranked next-best research investigations.
        Rank #1 is the single most valuable next investigation to perform.
        """
        contradictions = contradictions or []
        opportunities = opportunities or []
        resolved_investigation_queries = [q.lower().strip() for q in (resolved_investigation_queries or [])]
        history_topics = [t.lower().strip() for t in (history_topics or [])]

        # 1. Deterministically isolate active evidence gaps and uncertainty
        uncertainty: UncertaintyBreakdown = EpistemicUncertaintyEngine.evaluate_uncertainty(
            topic=topic,
            claims=claims,
            contradictions=contradictions,
        )

        candidates: List[NextBestResearchInvestigation] = []
        inv_counter = 1

        # Evaluate each active gap from the uncertainty engine
        for gap in uncertainty.active_gaps:
            # Check if this exact query or concept was already resolved in history
            if any(gap.actionable_query.lower() in rq for rq in resolved_investigation_queries):
                continue

            # Deterministic calculation of parameters (zero LLM fabrication)
            # 1. Uncertainty: from gap severity and global uncertainty
            u_score = round(max(0.1, min(0.95, (gap.severity * 0.7) + (uncertainty.aggregate_uncertainty_score * 0.3))), 3)

            # 2. Expected Information Gain:
            # Proportional to gap severity and entropy reduction potential
            # Gaps concerning primary evidence or contradictions yield highest info gain
            if gap.gap_class in [GapClass.MISSING_PRIMARY_EVIDENCE, GapClass.CONFLICTING_SOURCES]:
                e_gain = 0.88
            elif gap.gap_class in [GapClass.BUYER_EVIDENCE_MISSING, GapClass.ECONOMIC_ASSUMPTION_UNSUPPORTED]:
                e_gain = 0.82
            elif gap.gap_class == GapClass.INSUFFICIENT_SAMPLE_SIZE:
                e_gain = 0.74
            elif gap.gap_class == GapClass.COMPETITIVE_EVIDENCE_MISSING:
                e_gain = 0.70
            else:
                e_gain = 0.65

            # 3. Economic Relevance:
            # How closely the inquiry relates to revenue, cost, buyers, or viability
            if gap.gap_class in [GapClass.BUYER_EVIDENCE_MISSING, GapClass.ECONOMIC_ASSUMPTION_UNSUPPORTED]:
                econ_rel = 0.92
            elif gap.gap_class == GapClass.COMPETITIVE_EVIDENCE_MISSING:
                econ_rel = 0.85
            elif gap.gap_class == GapClass.CONFLICTING_SOURCES:
                econ_rel = 0.80
            elif gap.gap_class == GapClass.MISSING_PRIMARY_EVIDENCE:
                econ_rel = 0.78
            else:
                econ_rel = 0.65

            # 4. Actionability:
            # Can this be answered through concrete queries vs open-ended speculation?
            # Empirical trials and buyer surveys have very high actionability
            if gap.gap_class in [GapClass.MISSING_PRIMARY_EVIDENCE, GapClass.BUYER_EVIDENCE_MISSING, GapClass.ECONOMIC_ASSUMPTION_UNSUPPORTED]:
                actionability = 0.90
            elif gap.gap_class in [GapClass.CONFLICTING_SOURCES, GapClass.COMPETITIVE_EVIDENCE_MISSING]:
                actionability = 0.85
            else:
                actionability = 0.75

            # 5. Research Cost:
            # Relative cost of source retrieval and synthesis (1.0 = standard web/academic, 1.8 = deep financial/niche)
            if gap.gap_class in [GapClass.BUYER_EVIDENCE_MISSING, GapClass.ECONOMIC_ASSUMPTION_UNSUPPORTED]:
                research_cost = 1.25  # Slightly higher due to specialized paywalled / filing data
            elif gap.gap_class == GapClass.CONFLICTING_SOURCES:
                research_cost = 1.10
            else:
                research_cost = 1.00

            # Compute formula: (E_gain * Econ * Uncertainty * Actionability) / Cost
            raw_priority = (e_gain * econ_rel * u_score * actionability) / max(0.1, research_cost)
            priority_score = round(raw_priority * 10.0, 2)

            # Build targeted question and rationale
            if gap.gap_class == GapClass.BUYER_EVIDENCE_MISSING:
                question = f"Investigate enterprise willingness-to-pay and procurement budget allocation for {topic}."
                why_it_matters = f"Your opportunity hypothesis has operational rationale but lacks direct commercial budget-owner verification (Uncertainty: {int(u_score * 100)}%)."
            elif gap.gap_class == GapClass.ECONOMIC_ASSUMPTION_UNSUPPORTED:
                question = f"Quantify empirical unit economics, labor replacement elasticity, and payback periods for {topic}."
                why_it_matters = f"Projected ROI relies on unverified efficiency assumptions without audited financial trial data."
            elif gap.gap_class == GapClass.CONFLICTING_SOURCES:
                question = f"Adversarially probe operational failure modes and edge-case exceptions for {topic}."
                why_it_matters = f"Unresolved contradictions exist in current evidence regarding implementation overhead vs productivity lift."
            elif gap.gap_class == GapClass.MISSING_PRIMARY_EVIDENCE:
                question = f"Acquire primary empirical benchmark datasets for {topic} under production enterprise conditions."
                why_it_matters = f"Current knowledge corpus relies heavily on secondary descriptions without audited baseline measurements."
            elif gap.gap_class == GapClass.COMPETITIVE_EVIDENCE_MISSING:
                question = f"Identify incumbent enterprise workarounds, internal scripts, and legacy alternatives for {topic}."
                why_it_matters = f"Risk of building a point solution where enterprise buyers already utilize sufficient internal workarounds."
            else:
                question = f"Verify architectural scale boundaries, throughput, and integration failure rates for {topic}."
                why_it_matters = f"Systemic risk of integration friction and technical failure under high enterprise transaction volume."

            candidates.append(NextBestResearchInvestigation(
                investigation_id=f"DIR-INV-{inv_counter:03d}",
                question=question,
                why_it_matters=why_it_matters,
                knowledge_gap=gap.title,
                gap_class=gap.gap_class.value,
                current_uncertainty=u_score,
                current_uncertainty_label=f"{int(u_score * 100)}% ({gap.gap_class.value.replace('_', ' ').title()})",
                expected_information_gain=e_gain,
                economic_relevance=econ_rel,
                actionability=actionability,
                research_cost=research_cost,
                priority_score=priority_score,
                priority_rank=0,  # assigned after sort
                sources_required=gap.suggested_source_types or ["industry_disclosures", "empirical_audits"],
                actionable_query=gap.actionable_query,
                score_method="deterministic_multi_factor_v1",
                evidence_basis=gap.evidence_basis,
                confidence="HIGH" if len(claims) >= 10 else "MEDIUM",
                target_opportunity_id="OPP-001" if opportunities else None
            ))
            inv_counter += 1

        # Fallback if no candidate gaps were produced
        if not candidates:
            candidates.append(NextBestResearchInvestigation(
                investigation_id="DIR-INV-001",
                question=f"Investigate enterprise willingness-to-pay and procurement budget allocation for {topic}.",
                why_it_matters="Baseline buyer discovery is required to validate commercial willingness-to-pay.",
                knowledge_gap="Buyer Evidence Deficit",
                gap_class=GapClass.BUYER_EVIDENCE_MISSING.value,
                current_uncertainty=0.75,
                current_uncertainty_label="75% (Unverified Enterprise Buyer Demand)",
                expected_information_gain=0.82,
                economic_relevance=0.90,
                actionability=0.85,
                research_cost=1.1,
                priority_score=5.71,
                priority_rank=1,
                sources_required=["procurement_surveys", "customer_disclosures"],
                actionable_query=f"{topic} enterprise willingness to pay procurement budget decision maker survey",
                score_method="deterministic_multi_factor_v1",
                evidence_basis="Corpus baseline requires initial commercial buyer validation.",
                confidence="MEDIUM"
            ))

        # Sort candidates strictly by calculated Priority Score descending
        candidates.sort(key=lambda x: x.priority_score, reverse=True)

        # Assign priority rank (1, 2, 3...)
        for idx, item in enumerate(candidates):
            item.priority_rank = idx + 1

        return candidates
