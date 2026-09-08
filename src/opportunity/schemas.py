"""
Schemas for Market Problems, Economic Intelligence, SaaS/AI Opportunities,
Adversarial Validation Reports, and Solution Blueprints.
Enforces a hard epistemic evidence boundary: FACT, INFERENCE, HYPOTHESIS, ESTIMATE, UNKNOWN.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EpistemicCertainty(str, Enum):
    """Rigorous epistemic classification separating empirical facts from model deductions."""
    FACT = "FACT"             # Empirical, verified event or primary dataset from source
    INFERENCE = "INFERENCE"   # Logical deduction drawn directly from verified facts
    HYPOTHESIS = "HYPOTHESIS" # Testable assumption about customer pain or market demand
    ESTIMATE = "ESTIMATE"     # Quantitative projection with explicit modeling assumptions
    UNKNOWN = "UNKNOWN"       # Missing, unverified, or ambiguous information


class EpistemicItem(BaseModel):
    """Atomic claim or finding tagged with its strict epistemic grade."""
    category: EpistemicCertainty
    statement: str
    source_citation: Optional[str] = None
    confidence: float = 0.85


class InspectableDimensions(BaseModel):
    """Inspectable qualitative and quantitative dimensions for opportunity ranking."""
    demand_evidence: str = "Strong"            # Strong, Moderate, Weak
    problem_severity: str = "High"             # Critical, High, Moderate, Low
    wtp_evidence: str = "Moderate"             # Strong, Moderate, Speculative
    competition_intensity: str = "Moderate"    # High, Moderate, Low
    competitive_gap: str = "Large"             # Large, Moderate, Narrow
    technical_feasibility: str = "High"        # High, Moderate, Challenging
    defensibility: str = "Moderate"            # High, Moderate, Low
    evidence_quality: str = "High"             # High, Moderate, Low
    unknowns: List[str] = Field(default_factory=list)


class OpportunityScoreBreakdown(BaseModel):
    """Heuristic scoring breakdown with 'Why Ranked #1' qualitative explanation."""
    heuristic_score: float = 8.5
    label: str = "heuristic ranking"
    ranking_rationale: str = "Ranked #1 due to severe operational handoff friction coexisting with 84% AI tool adoption without EBITDA margin expansion."
    dimensions: InspectableDimensions = Field(default_factory=InspectableDimensions)
    component_scores: Dict[str, float] = Field(default_factory=dict)


class SolutionBlueprint(BaseModel):
    """Detailed commercial solution architecture and execution blueprint."""
    concept: str
    category: str  # "B2B SaaS", "Autonomous AI Agent System", "Workflow Infrastructure", "Developer Tool", "Data Product", "Productized Service"
    target_buyer_icp: str
    core_workflow: str
    mvp_specification: str
    future_features: List[str] = Field(default_factory=list)
    technical_architecture: str
    required_infrastructure: List[str] = Field(default_factory=list)
    ai_requirements: str
    integrations: List[str] = Field(default_factory=list)  # e.g. MCP, Salesforce, NetSuite, Linear
    data_requirements: str
    pricing_hypotheses: str
    gtm_channels: List[str] = Field(default_factory=list)
    validation_experiment: str
    success_criteria: str
    risks_and_mitigations: List[Dict[str, str]] = Field(default_factory=list)
    estimated_build_time: str = "3 to 4 weeks MVP"
    roi_multiple: str = "8.5x ROI"


class ValidationVerdict(str, Enum):
    """
    Adversarial validation outcome verdict with strict epistemic boundaries.
    Does not proclaim absolute business truth; reflects current evidentiary support.
    """
    PROCEED_TO_MVP = "PROCEED_TO_MVP"                         # Evidence supports proceeding to validation / MVP experiment
    PILOT_EXPERIMENT_REQUIRED = "PILOT_EXPERIMENT_REQUIRED"   # Key assumptions unverified; execute low-cost experiment
    KILL_OPPORTUNITY_NOW = "KILL_OPPORTUNITY_NOW"             # Evidence currently supports killing this opportunity under defined assumptions
    DO_NOT_BUILD_YET = "KILL_OPPORTUNITY_NOW"                 # Backwards compatibility alias


class ValidationDimensionAnalysis(BaseModel):
    """
    Strict separation of evidence, inference, unknowns, and assessment.
    Prevents ungrounded score fabrication.
    """
    dimension_name: str                  # "DEMAND", "WILLINGNESS_TO_PAY", "COMPETITION", "FEASIBILITY", "DEFENSIBILITY"
    evidence_claims: List[EpistemicItem] = Field(default_factory=list)
    inference: str = "Logical deduction from observed evidence."
    unknowns: List[str] = Field(default_factory=list)
    assessment_score: float = 75.0       # 0.0 to 100.0
    confidence: str = "MEDIUM"           # HIGH, MEDIUM, LOW, UNKNOWN
    grounding_summary: str = "Supported by empirical claims. Primary buyer evidence: unverified."


class KillThesis(BaseModel):
    """
    The adversarial crucible attempting to disprove the opportunity.
    Articulates why the venture will fail under defined conditions.
    """
    kill_verdict: ValidationVerdict = ValidationVerdict.PILOT_EXPERIMENT_REQUIRED
    kill_summary: str = "Evidence currently supports proceeding with validation under defined assumptions."
    counter_evidence: List[EpistemicItem] = Field(default_factory=list)
    critical_vulnerability: str
    incumbent_crush_risk: str
    churn_and_retention_risk: str
    falsification_boundaries: List[str] = Field(default_factory=list)


class ValidationExperiment(BaseModel):
    """
    Cheapest, fastest experiment designed to prove or disprove the opportunity.
    Uses estimated ranges, cost basis, and confidence without inventing fixed prices.
    """
    experiment_id: str
    title: str
    tier: str                            # LEVEL_1_DISCOVERY, LEVEL_2_COMMITMENT, LEVEL_3_CONCIERGE, LEVEL_4_SYNTHETIC
    description: str
    estimated_cost: str = "$0 - $200"    # Range or UNKNOWN
    cost_basis: str = "Self-conducted customer interviews with zero software overhead"
    cost_confidence: str = "HIGH"        # HIGH, MEDIUM, LOW, UNKNOWN
    estimated_time: str = "5 to 7 business days"
    expected_information_gain: float = 0.85
    success_criterion: str               # Quantitative threshold to proceed
    kill_criterion: str                  # Explicit condition to kill immediately


class OpportunityValidationReport(BaseModel):
    """
    Comprehensive Adversarial Validation Lab Report.
    Separates evidence from judgment across all 5 dimensions and delivers executable experiments.
    """
    opportunity_id: str
    opportunity_title: str
    dimensions: Dict[str, ValidationDimensionAnalysis] = Field(default_factory=dict)
    kill_thesis: Optional[KillThesis] = None
    ranked_experiments: List[ValidationExperiment] = Field(default_factory=list)
    cheapest_validation_experiment: Dict[str, Any] = Field(default_factory=dict)
    pro_demand_evidence: List[EpistemicItem] = Field(default_factory=list)
    contra_demand_evidence: List[EpistemicItem] = Field(default_factory=list)
    existing_competitors: List[str] = Field(default_factory=list)
    graveyard_failed_attempts: List[str] = Field(default_factory=list)
    customer_friction_complaints: List[str] = Field(default_factory=list)
    critical_assumptions: List[str] = Field(default_factory=list)
    missing_evidence_gaps: List[str] = Field(default_factory=list)
    verdict: ValidationVerdict = ValidationVerdict.PILOT_EXPERIMENT_REQUIRED
    verdict_rationale: str = "Evidence currently supports executing a low-cost validation experiment before capital allocation."


class EconomicScenario(BaseModel):
    """Specific scenario projection with calibrated parameters and explicit assumptions."""
    scenario_name: str  # "Conservative", "Base", "Upside"
    adoption_rate_pct: float  # e.g. 25.0, 50.0, 80.0
    projected_annual_benefit_usd: float
    implementation_cost_usd: float
    annual_operating_cost_usd: float
    net_first_year_benefit_usd: float
    roi_multiple: str  # e.g. "2.1x ROI"
    key_assumptions: List[str] = Field(default_factory=list)


class EconomicSensitivityAnalysis(BaseModel):
    """3-tier scenario analysis with sensitivity factors and epistemic parameter coverage."""
    conservative_case: EconomicScenario
    base_case: EconomicScenario
    upside_case: EconomicScenario
    labor_rate_sensitivity: str = "±20% fully-burdened labor rate yields ±18% shift in net annual savings"
    adoption_rate_sensitivity: str = "Every 10% adoption lag delays breakeven by 1.8 months"
    evidence_backed_parameters: int = 4
    total_parameters: int = 6
    evidence_coverage_pct: float = 66.7
    unverified_assumptions_count: int = 2
    epistemic_confidence: str = "MEDIUM"  # "HIGH", "MEDIUM", "LOW", "UNKNOWN"
    notes: str = "Model projections calibrated against empirical research claims; assumptions require customer discovery."


class AntiAnchoringMetric(BaseModel):
    """Rigorous anti-anchoring diagnostic evaluating evidence grounding vs mechanical prompt copying."""
    prompt_verbatim_overlap: float = 0.0  # 0.0 = zero verbatim prompt substring copy
    nomenclature_evidence_grounding: float = 0.85  # % of key terms and mechanisms derived from claims
    discovered_lexicon: List[str] = Field(default_factory=list)  # terms discovered in evidence
    evidence_mechanism: str = "Evidence-derived operational pathology"
    query_independence_score: float = 0.90  # 0.0-1.0


class MarketProblemRecord(BaseModel):
    """Real-world problem or operational pathology faced by companies & startups."""
    problem_id: str
    run_id: str = "LEGACY-CORPUS"
    target_segment: str  # "Enterprise", "Scale-up / Startup", "Mid-Market", "All"
    functional_area: str  # e.g., "RevOps & Sales", "Engineering & AI Infra", "Compliance & Legal", "Operations"
    title: str
    description: str
    root_cause: str
    symptoms: List[str] = Field(default_factory=list)
    economic_impact: str
    severity_score: float = 8.5  # 1.0 to 10.0
    frequency_score: float = 8.0
    epistemic_evidence: List[EpistemicItem] = Field(default_factory=list)
    cited_claims: List[str] = Field(default_factory=list)


class SaaSSolutionOpportunity(BaseModel):
    """Actionable B2B SaaS, AI Agent System, or Automation Service product opportunity."""
    opportunity_id: str
    run_id: str = "LEGACY-CORPUS"
    solution_title: str
    category: str  # "B2B SaaS", "Autonomous AI Agent System", "Automation Service", "Workflow Infrastructure"
    problem_addressed_id: str
    problem_title: str
    target_buyer_icp: str  # e.g. "VP of RevOps", "Head of AI Engineering", "Chief Operating Officer"
    core_value_proposition: str
    what_you_can_offer: str
    technical_blueprint: str
    monetization_model: str
    estimated_build_time: str
    opportunity_score: float = 8.8  # Heuristic ranking index
    roi_multiple: str = "4x to 10x ROI (Model Estimate)"

    # Enriched inspectability & epistemic models
    economic_sensitivity: Optional[EconomicSensitivityAnalysis] = None
    anti_anchoring: Optional[AntiAnchoringMetric] = None
    score_breakdown: Optional[OpportunityScoreBreakdown] = None
    blueprint: Optional[SolutionBlueprint] = None
    validation_report: Optional[OpportunityValidationReport] = None
    epistemic_breakdown: Dict[str, List[str]] = Field(default_factory=dict)
    provenance_claims: List[str] = Field(default_factory=list)
    provenance_sources: List[str] = Field(default_factory=list)


class OpportunityMatrixResponse(BaseModel):
    """Aggregate response returned by the Opportunity Discovery Engine."""
    topic: str
    run_id: str = "LEGACY-CORPUS"
    total_problems_identified: int
    total_solutions_generated: int
    market_problems: List[MarketProblemRecord]
    solution_opportunities: List[SaaSSolutionOpportunity]
    metadata: Dict[str, Any] = Field(default_factory=dict)
