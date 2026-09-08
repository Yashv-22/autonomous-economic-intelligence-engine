"""
Pydantic Data Models & Schemas for Autonomous AI Operating-Model Intelligence System.
Defines foundational schemas for Provenance, Ingestion, Claim Extraction, Contradiction Detection,
Problem Hypotheses, Knowledge Representation, and Model/Tool Interfaces.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class EvidenceGrade(str, Enum):
    """Epistemic classification of research claims."""
    FACT = "FACT"                     # Formally verifiable technical standard, statutory law, or math theorem
    EVIDENCE = "EVIDENCE"             # Sourced survey data, published case study, or empirical trial
    INFERENCE = "INFERENCE"           # Deductive reasoning derived from multiple corroborated evidence points
    HYPOTHESIS = "HYPOTHESIS"         # Theoretical proposition requiring empirical experimental validation
    ASSUMPTION = "ASSUMPTION"         # Explicit parameter chosen for modeling purposes
    RECOMMENDATION = "RECOMMENDATION" # Prescriptive operational or architectural guidance


class ContradictionType(str, Enum):
    """Taxonomy of cross-source contradictions."""
    DIRECT_OPPOSITION = "DIRECT_OPPOSITION"                   # Source A directly contradicts Source B factually
    PROJECTION_VS_REALITY = "PROJECTION_VS_REALITY"           # Vendor/bullish projection vs. empirical analyst finding
    ASSUMPTION_VS_EVIDENCE = "ASSUMPTION_VS_EVIDENCE"         # Model assumption unsupported or weakened by evidence
    MAGNITUDE_DISCREPANCY = "MAGNITUDE_DISCREPANCY"           # Substantial divergence in claimed ROI or velocity uplift


class PolarityType(str, Enum):
    """Sentiment polarity towards AI operating model transformation."""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class ToolPermission(str, Enum):
    """Permission classification for system tools."""
    READ_ONLY = "READ_ONLY"             # Pure data retrieval, search, inspection (No side effects)
    STATE_CHANGING = "STATE_CHANGING"   # Modifies knowledge base or cache
    HIGH_RISK = "HIGH_RISK"             # Network egress, model fine-tuning, system reconfiguration


class SourceSpan(BaseModel):
    """Cryptographically anchored document or web text span."""
    document_name: str = Field(..., description="Filename, URL, or identifier of the source document")
    document_hash: str = Field(..., description="SHA-256 hash of the full source document")
    page_or_section: str = Field(..., description="Page number or section header where span occurs")
    paragraph_index: int = Field(..., description="0-indexed paragraph order within document")
    text: str = Field(..., description="Exact extracted verbatim text snippet")
    span_hash: str = Field(..., description="SHA-256 hash of the exact span text")
    source_url: Optional[str] = Field(None, description="Original source URL if acquired via web")
    start_char: Optional[int] = Field(None, description="Starting character offset in source")
    end_char: Optional[int] = Field(None, description="Ending character offset in source")
    run_id: str = Field(default="LEGACY-CORPUS", description="Research run identifier, e.g. RUN-20260906-173500")


class ProvenanceMetadata(BaseModel):
    """Full acquisition and lineage metadata for an ingested artifact."""
    source_url: Optional[str] = Field(None, description="Original web address")
    canonical_url: Optional[str] = Field(None, description="Canonical normalized URL")
    domain: Optional[str] = Field(None, description="Source domain e.g. mckinsey.com")
    publisher: Optional[str] = Field(None, description="Publishing organization or institution")
    author: Optional[str] = Field(None, description="Author or analyst if stated")
    publication_date: Optional[str] = Field(None, description="ISO date of document publication")
    retrieval_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of acquisition"
    )
    document_hash: str = Field(..., description="SHA-256 hash of raw acquired artifact")
    content_hash: str = Field(..., description="SHA-256 hash of extracted clean text")
    source_type: str = Field(default="document", description="pdf, docx, web_html, text, api")
    acquisition_method: str = Field(default="filesystem", description="filesystem, search_tool, fetch_tool")
    license: Optional[str] = Field(None, description="Access / copyright terms")


class ExtractedClaim(BaseModel):
    """Structured research claim extracted from document spans."""
    claim_id: str = Field(..., description="Unique claim identifier, e.g., CLAIM-0001")
    text: str = Field(..., description="Concise statement of the extracted claim")
    entity_or_topic: str = Field(..., description="Primary organizational topic or institution")
    evidence_grade: EvidenceGrade = Field(..., description="Epistemic grading of the claim")
    institution: Optional[str] = Field(None, description="Originating institution (McKinsey, BCG, Bain, etc.)")
    quantitative_metric: Optional[str] = Field(None, description="Specific numerical figure if present (e.g. '88%')")
    is_model_assumption: bool = Field(False, description="True if claim is an internal model assumption rather than external fact")
    source_span: SourceSpan = Field(..., description="Cryptographic source provenance reference")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")
    tags: List[str] = Field(default_factory=list, description="Categorization tags (e.g. ['routing', 'governance'])")
    polarity: PolarityType = Field(default=PolarityType.NEUTRAL, description="POSITIVE, NEGATIVE, or NEUTRAL")
    run_id: str = Field(default="LEGACY-CORPUS", description="Research run identifier")
    canonical_fingerprint: Optional[str] = Field(None, description="Multi-field canonical fingerprint for deduplication")
    citation_count: int = Field(default=1, description="Number of distinct corroborating sources citing this canonical claim")


class ContradictionRecord(BaseModel):
    """Identified cross-source tension, contradiction, or unsupported assumption."""
    contradiction_id: str = Field(..., description="Unique identifier, e.g., CONTRA-0001")
    topic: str = Field(..., description="Domain or topic of tension")
    claim_a: ExtractedClaim = Field(..., description="First claim in tension")
    claim_b: ExtractedClaim = Field(..., description="Second opposing claim in tension")
    contradiction_type: ContradictionType = Field(..., description="Taxonomy classification of contradiction")
    explanation: str = Field(..., description="Detailed explanation of the analytical discrepancy")
    severity: float = Field(default=5.0, ge=1.0, le=10.0, description="Severity score of the tension")
    conflict_status: str = Field(default="PRESERVED", description="Status (PRESERVED, RESOLVED, DISCONFIRMED)")
    run_id: str = Field(default="LEGACY-CORPUS", description="Research run identifier")


class ProblemHypothesis(BaseModel):
    """Falsifiable problem hypothesis generated from evidence and contradictions."""
    hypothesis_id: str = Field(..., description="Unique identifier, e.g., HYPO-0001")
    title: str = Field(..., description="Descriptive title of the hypothesized problem")
    statement: str = Field(..., description="Formal problem statement")
    null_hypothesis: str = Field(..., description="Null hypothesis (conditions for falsification)")
    supporting_claim_ids: List[str] = Field(default_factory=list, description="IDs of claims supporting hypothesis")
    opposing_claim_ids: List[str] = Field(default_factory=list, description="IDs of claims opposing hypothesis")
    affected_functions: List[str] = Field(default_factory=list, description="Organizational departments affected")
    falsification_criteria: str = Field(..., description="Concrete empirical test that would disprove hypothesis")
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Confidence in hypothesis validity")
    run_id: str = Field(default="LEGACY-CORPUS", description="Research run identifier")


class ResearchObjective(BaseModel):
    """Formal research objective driving autonomous discovery and acquisition."""
    objective_id: str = Field(..., description="Unique ID, e.g. OBJ-0001")
    query: str = Field(..., description="Primary research query / question")
    topic: str = Field(..., description="Target domain / topic")
    max_depth: int = Field(default=2, ge=1, le=5, description="Search recursion depth")
    budget_sources: int = Field(default=5, ge=1, le=20, description="Max sources to ingest")
    allowed_domains: Optional[List[str]] = Field(None, description="Optional domain whitelist")
    run_id: Optional[str] = Field(None, description="Optional explicit research run ID")


class ResearchGap(BaseModel):
    """Identified evidentiary deficit or unanswered variable."""
    gap_id: str = Field(..., description="Unique identifier, e.g. GAP-0001")
    topic: str = Field(..., description="Domain topic missing evidence")
    description: str = Field(..., description="Detailed description of what evidence is missing")
    missing_variable: str = Field(..., description="Specific parameter or variable needed")
    suggested_query: str = Field(..., description="Suggested search query to resolve gap")
    priority: float = Field(default=5.0, ge=1.0, le=10.0, description="Priority score")


class EpistemicScorecard(BaseModel):
    """Rigorous epistemic research scorecard with documented calculations and explicit UNKNOWN fallbacks."""
    source_diversity_score: Optional[float] = None
    source_diversity_label: str = "UNKNOWN"
    primary_source_ratio: Optional[float] = None
    cross_source_corroboration_ratio: Optional[float] = None
    contradiction_density: float = 0.0
    opportunity_conviction: str = "UNKNOWN"
    notes: Dict[str, str] = Field(default_factory=dict)


class SynthesisResult(BaseModel):
    """Evidence-backed analytical synthesis answering a research objective."""
    synthesis_id: str = Field(..., description="Unique synthesis ID")
    objective_id: str = Field(..., description="Referenced research objective ID")
    title: str = Field(..., description="Synthesis title")
    summary: str = Field(..., description="Concise executive summary")
    detailed_findings: List[str] = Field(default_factory=list, description="Structured finding bullet points")
    supporting_claim_ids: List[str] = Field(default_factory=list, description="IDs of supporting claims")
    cited_span_hashes: List[str] = Field(default_factory=list, description="Cryptographic span hashes cited")
    contradictions_noted: List[str] = Field(default_factory=list, description="Contradiction IDs referenced")
    unresolved_gaps: List[str] = Field(default_factory=list, description="Remaining research gaps")
    epistemic_confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Overall confidence")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProblemDossier(BaseModel):
    """Aggregated, human-auditable Problem & Intelligence Dossier."""
    dossier_id: str = Field(..., description="Dossier UUID or identifier")
    run_id: str = Field(default="LEGACY-CORPUS", description="Research run identifier")
    title: str = Field(default="Operating Model Intelligence: Problem & Research Dossier")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_documents_ingested: int = Field(..., description="Count of ingested source documents")
    total_claims_extracted: int = Field(..., description="Total structured claims extracted")
    claims_by_grade: Dict[str, int] = Field(default_factory=dict, description="Histogram of claims by evidence grade")
    verified_contradictions: List[ContradictionRecord] = Field(default_factory=list, description="Detected contradictions")
    hypothesized_problems: List[ProblemHypothesis] = Field(default_factory=list, description="Formulated problem hypotheses")
    merkle_provenance_root: str = Field(..., description="SHA-256 master provenance root of all ingested span hashes")
    synthesis: Optional[SynthesisResult] = Field(None, description="Optional high-level analytical synthesis")
    epistemic_scorecard: Optional[EpistemicScorecard] = Field(None, description="Epistemic scorecard with UNKNOWN fallbacks")


class AuditRecord(BaseModel):
    """Immutable audit trail entry for an operation with sequential cryptographic chain linking."""
    audit_id: str = Field(..., description="Audit record UUID")
    run_id: str = Field(default="LEGACY-CORPUS", description="Research run identifier")
    correlation_id: str = Field(..., description="Correlation ID tracing request")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sequence_index: int = Field(default=0, description="Sequential position in audit chain")
    action: str = Field(..., description="Action name e.g. INGEST_DOC, EXTRACT_CLAIMS, INVOKE_TOOL")
    actor: str = Field(..., description="Agent or component ID performing action")
    input_hash: str = Field(..., description="SHA-256 of input parameters")
    output_hash: str = Field(..., description="SHA-256 of output artifact or result")
    previous_chain_hash: str = Field(default="0" * 64, description="SHA-256 hash of previous audit record in chain")
    chain_hash: str = Field(default="", description="Current block hash: SHA256(H_{n-1} + canonical_payload)")
    verification_status: str = Field(default="LEGACY / PRE-V2.6", description="'CHAIN VERIFIED' or 'LEGACY / PRE-V2.6'")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="SUCCESS", description="SUCCESS or FAILED")


class ToolResult(BaseModel):
    """Standardized tool execution result."""
    tool_name: str
    success: bool = Field(..., description="True if tool executed without error")
    data: Any = Field(None, description="Tool output payload or string")
    output: Any = Field(None, description="Tool output alias for compatibility")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time_ms: float = Field(default=0.0, description="Execution duration in ms")
    output_summary: Optional[str] = Field(None, description="Human readable summary")
    metadata: Dict[str, Any] = Field(default_factory=dict)



class TokenUsage(BaseModel):
    """Token accounting record for LLM calls."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class ModelResponse(BaseModel):
    """Standardized response from Model Gateway."""
    model_name: str
    provider: str
    content: str
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    raw_response: Optional[Dict[str, Any]] = None


class SourceState(str, Enum):
    DISCOVERED = "DISCOVERED"
    ACQUIRED = "ACQUIRED"
    PARSED = "PARSED"
    CITED = "CITED"
    VERIFIED = "VERIFIED"


class ResearchSourceExcerpt(BaseModel):
    """Verbatim text excerpt strictly preserved from original source span."""
    span_hash: str
    page_or_section: str
    text: str
    quote_type: str = "DIRECT_QUOTE"


class ResearchSourceEntry(BaseModel):
    """Auditable bibliography source with exact URL availability and verbatim span provenance."""
    source_id: str
    citation_index: int
    title: str
    document_name: str
    url: Optional[str] = None
    domain: str
    status: str = "ACQUIRED"
    source_type: str = "WEB_DOCUMENT"
    retrieved_at: str
    document_hash: str
    total_spans: int = 0
    claims_count: int = 0
    sample_excerpts: List[ResearchSourceExcerpt] = Field(default_factory=list)


class ResearchDossierSection(BaseModel):
    """Thematic section in the intelligence article."""
    section_id: str
    title: str
    lead_paragraph: str
    paragraphs: List[str] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    cited_claim_ids: List[str] = Field(default_factory=list)
    citation_numbers: List[int] = Field(default_factory=list)


class ResearchMethodology(BaseModel):
    """Explicit methodology and epistemic limitations of the research run."""
    objective_query: str
    run_id: str
    acquisition_pipeline: str = "Autonomous Web Crawler + Cryptographic Parser"
    total_sources_scanned: int = 0
    total_spans_indexed: int = 0
    total_claims_verified: int = 0
    model_involvement: str = "Evidence extraction, epistemic grading, and claim attribution"
    epistemic_grade_breakdown: Dict[str, int] = Field(default_factory=dict)
    known_limitations: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)


class ResearchDossierReport(BaseModel):
    """Comprehensive, human-auditable Wikipedia-style research dossier."""
    topic: str
    run_id: str
    dossier_id: str
    generated_at: str
    merkle_provenance_root: str
    epistemic_confidence_level: str = "UNKNOWN"
    epistemic_scorecard: Optional[EpistemicScorecard] = None
    reading_time_minutes: int = 3
    stats: Dict[str, Any] = Field(default_factory=dict)
    tldr_summary: List[str] = Field(default_factory=list)
    executive_synthesis: str = ""
    thematic_sections: List[ResearchDossierSection] = Field(default_factory=list)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    methodology: Optional[ResearchMethodology] = None
    sources: List[ResearchSourceEntry] = Field(default_factory=list)
    raw_markdown: str = ""


class SummarizeRequest(BaseModel):
    """Request for on-demand evidence-locked summarization."""
    topic: str = "Enterprise AI Operating Model Redesign"
    run_id: Optional[str] = None
    mode: str = "tldr"  # "tldr" | "executive" | "deep"
    custom_focus: Optional[str] = None


class SummarizeResponse(BaseModel):
    """Evidence-locked summarization response."""
    success: bool = True
    mode: str
    summary: str
    model: str
    provider: str
    run_id: str
    source_claims_used: int
    generated_at: str

