"""
Test Cross-Run State Contamination & Epistemic Isolation (Engine V2.6 Directive #9)
Asserts:
- Run A: AI implementation across departments
- Run B: Customer churn in SaaS
- Run C: Manufacturing inventory inefficiency
- B cannot inherit A's opportunities, terminology, economic assumptions, sources/spans
- C cannot inherit A/B's opportunities, terminology, economics, sources/spans
- Persistent KB preserves all historical and multi-run claims with canonical deduplication
- Audit chain preserves sequential cryptographic continuity without fake history
"""

import pytest
import os
import shutil
from datetime import datetime, timezone
from src.knowledge.relational import SQLiteRelationalStore
from src.opportunity.engine import OpportunityDiscoveryEngine
from src.models.schemas import (
    SourceSpan,
    ExtractedClaim,
    EvidenceGrade,
    PolarityType,
    ContradictionRecord,
    ProblemHypothesis,
    ContradictionType,
    AuditRecord,
)


@pytest.fixture
def clean_test_store(tmp_path):
    db_path = os.path.join(tmp_path, "test_contamination_ledger.db")
    store = SQLiteRelationalStore(db_path=db_path)
    return store


def test_cross_run_state_contamination_and_isolation(clean_test_store):
    store = clean_test_store
    opp_engine = OpportunityDiscoveryEngine()

    run_a_id = "RUN-20260906-100001"
    run_b_id = "RUN-20260906-100002"
    run_c_id = "RUN-20260906-100003"

    # -------------------------------------------------------------
    # 1. RUN A: Enterprise AI Operating Model & Workflow Routing
    # -------------------------------------------------------------
    span_a = SourceSpan(
        document_name="mckinsey_ai_operating_model.pdf",
        document_hash="hash_a_123",
        page_or_section="p.12",
        paragraph_index=1,
        text="84% of corporate AI transformations stall due to human-in-the-loop task routing handoffs.",
        span_hash="span_hash_a1",
        run_id=run_a_id,
    )
    claim_a = ExtractedClaim(
        claim_id="CLM-A1",
        text="84% of corporate AI transformations stall due to human-in-the-loop task routing handoffs.",
        entity_or_topic="Enterprise AI Transformation",
        evidence_grade=EvidenceGrade.EVIDENCE,
        institution="McKinsey & Co",
        quantitative_metric="84% stall rate",
        source_span=span_a,
        confidence_score=0.92,
        polarity=PolarityType.NEGATIVE,
        run_id=run_a_id,
    )
    store.persist_all(
        spans=[span_a],
        claims=[claim_a],
        contradictions=[],
        hypotheses=[],
        run_id=run_a_id,
    )

    # Log audit event for Run A
    store.log_audit_record(
        AuditRecord(
            audit_id="AUD-RUN-A",
            correlation_id="CORR-RUN-A",
            run_id=run_a_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            action="EXECUTE_RESEARCH_RUN_A",
            actor="DirectorAgent",
            input_hash="hash_input_a",
            output_hash="hash_output_a",
        )
    )

    # Discover opportunities for Run A
    claims_a = store.get_claims(run_id=run_a_id)
    matrix_a = opp_engine.discover_opportunities(
        claims=claims_a,
        topic="Enterprise AI Implementation Across Departments",
        run_id=run_a_id,
    )

    # Assertions on Run A
    assert len(matrix_a.solution_opportunities) > 0
    opp_a_titles = [o.solution_title for o in matrix_a.solution_opportunities]
    opp_a_text = " ".join(opp_a_titles + [o.core_value_proposition for o in matrix_a.solution_opportunities]).lower()
    assert "arbitration" in opp_a_text or "workflow" in opp_a_text or "governance" in opp_a_text

    # -------------------------------------------------------------
    # 2. RUN B: B2B SaaS Customer Churn & Retention Intelligence
    # -------------------------------------------------------------
    span_b = SourceSpan(
        document_name="gainsight_saas_churn_metrics.pdf",
        document_hash="hash_b_456",
        page_or_section="Section 4",
        paragraph_index=2,
        text="B2B SaaS net revenue retention drops by 18% when product adoption telemetry triggers false positive churn alerts.",
        span_hash="span_hash_b1",
        run_id=run_b_id,
    )
    claim_b = ExtractedClaim(
        claim_id="CLM-B1",
        text="B2B SaaS net revenue retention drops by 18% when product adoption telemetry triggers false positive churn alerts.",
        entity_or_topic="B2B SaaS Churn",
        evidence_grade=EvidenceGrade.EVIDENCE,
        institution="Gainsight Customer Success Benchmark",
        quantitative_metric="18% NRR drop",
        source_span=span_b,
        confidence_score=0.90,
        polarity=PolarityType.NEGATIVE,
        run_id=run_b_id,
    )
    store.persist_all(
        spans=[span_b],
        claims=[claim_b],
        contradictions=[],
        hypotheses=[],
        run_id=run_b_id,
    )

    # Log audit event for Run B
    store.log_audit_record(
        AuditRecord(
            audit_id="AUD-RUN-B",
            correlation_id="CORR-RUN-B",
            run_id=run_b_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            action="EXECUTE_RESEARCH_RUN_B",
            actor="DirectorAgent",
            input_hash="hash_input_b",
            output_hash="hash_output_b",
        )
    )

    # Discover opportunities for Run B isolated to run_b_id
    claims_b = store.get_claims(run_id=run_b_id)
    matrix_b = opp_engine.discover_opportunities(
        claims=claims_b,
        topic="Customer Churn in SaaS",
        run_id=run_b_id,
    )

    # STRICT DIRECTIVE #9 ASSERTIONS: Run B vs Run A Contamination
    assert len(claims_b) == 1
    assert claims_b[0].run_id == run_b_id
    assert claims_b[0].claim_id != claim_a.claim_id
    assert claims_b[0].source_span.span_hash != span_a.span_hash

    # B cannot inherit A's opportunities
    opp_b_titles = [o.solution_title for o in matrix_b.solution_opportunities]
    for b_title in opp_b_titles:
        assert b_title not in opp_a_titles

    # B cannot inherit A's terminology or department routing mechanics
    opp_b_text = " ".join(opp_b_titles + [o.core_value_proposition for o in matrix_b.solution_opportunities]).lower()
    assert "churn" in opp_b_text or "retention" in opp_b_text or "saas" in opp_b_text
    assert "departmental ai" not in opp_b_text
    assert "human-in-the-loop task routing" not in opp_b_text

    # B's economic assumptions cannot inherit A's claims
    for opp_b in matrix_b.solution_opportunities:
        assert opp_b.run_id == run_b_id
        if opp_b.anti_anchoring:
            assert opp_b.anti_anchoring.prompt_verbatim_overlap == 0.0

    # -------------------------------------------------------------
    # 3. RUN C: Manufacturing Inventory Inefficiency & Supply Chain
    # -------------------------------------------------------------
    span_c = SourceSpan(
        document_name="supply_chain_quarterly.pdf",
        document_hash="hash_c_789",
        page_or_section="p.45",
        paragraph_index=3,
        text="Manufacturing stockouts increase carrying costs by 32% due to legacy ERP reconciliation batch delays.",
        span_hash="span_hash_c1",
        run_id=run_c_id,
    )
    claim_c = ExtractedClaim(
        claim_id="CLM-C1",
        text="Manufacturing stockouts increase carrying costs by 32% due to legacy ERP reconciliation batch delays.",
        entity_or_topic="Manufacturing Supply Chain",
        evidence_grade=EvidenceGrade.EVIDENCE,
        institution="Supply Chain Management Institute",
        quantitative_metric="32% carrying cost increase",
        source_span=span_c,
        confidence_score=0.88,
        polarity=PolarityType.NEGATIVE,
        run_id=run_c_id,
    )
    store.persist_all(
        spans=[span_c],
        claims=[claim_c],
        contradictions=[],
        hypotheses=[],
        run_id=run_c_id,
    )

    # Log audit event for Run C
    store.log_audit_record(
        AuditRecord(
            audit_id="AUD-RUN-C",
            correlation_id="CORR-RUN-C",
            run_id=run_c_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            action="EXECUTE_RESEARCH_RUN_C",
            actor="DirectorAgent",
            input_hash="hash_input_c",
            output_hash="hash_output_c",
        )
    )

    # Discover opportunities for Run C isolated to run_c_id
    claims_c = store.get_claims(run_id=run_c_id)
    matrix_c = opp_engine.discover_opportunities(
        claims=claims_c,
        topic="Manufacturing Inventory Inefficiency",
        run_id=run_c_id,
    )

    # STRICT DIRECTIVE #9 ASSERTIONS: Run C vs Run A & B Contamination
    assert len(claims_c) == 1
    assert claims_c[0].run_id == run_c_id
    assert claims_c[0].claim_id not in [claim_a.claim_id, claim_b.claim_id]

    opp_c_titles = [o.solution_title for o in matrix_c.solution_opportunities]
    for c_title in opp_c_titles:
        assert c_title not in opp_a_titles
        assert c_title not in opp_b_titles

    opp_c_text = " ".join(opp_c_titles + [o.core_value_proposition for o in matrix_c.solution_opportunities]).lower()
    assert "inventory" in opp_c_text or "erp" in opp_c_text or "supply" in opp_c_text or "manufacturing" in opp_c_text
    assert "churn" not in opp_c_text
    assert "retention intelligence" not in opp_c_text
    assert "departmental ai" not in opp_c_text

    # -------------------------------------------------------------
    # 4. PERSISTENT KB & DEDUPLICATION CHECKS
    # -------------------------------------------------------------
    # All 3 runs must contribute knowledge to the persistent KB
    all_claims = store.get_claims()
    assert len(all_claims) == 3

    # Counts per run must be exactly 1
    counts_a = store.get_corpus_counts(run_id=run_a_id)
    counts_b = store.get_corpus_counts(run_id=run_b_id)
    counts_c = store.get_corpus_counts(run_id=run_c_id)
    assert counts_a["current_run_claims"] == 1
    assert counts_b["current_run_claims"] == 1
    assert counts_c["current_run_claims"] == 1
    assert counts_a["historical_records"] == 3
    assert counts_a["persistent_deduplicated"] == 3

    # Corroborating duplicate claim in Run C with identical semantic fields
    claim_c_corroborating = ExtractedClaim(
        claim_id="CLM-C2-CORROB",
        text="Manufacturing stockouts increase carrying costs by 32% due to legacy ERP reconciliation batch delays.",
        entity_or_topic="Manufacturing Supply Chain",
        evidence_grade=EvidenceGrade.EVIDENCE,
        institution="Gartner Supply Chain Review",
        quantitative_metric="32% carrying cost increase",
        source_span=SourceSpan(
            document_name="gartner_inventory_study.pdf",
            document_hash="hash_gartner",
            page_or_section="p.3",
            paragraph_index=1,
            text="Manufacturing stockouts increase carrying costs by 32% due to legacy ERP reconciliation batch delays.",
            span_hash="span_hash_gartner_c",
            run_id=run_c_id,
        ),
        confidence_score=0.95,
        polarity=PolarityType.NEGATIVE,
        run_id=run_c_id,
    )
    store.persist_all(
        spans=[claim_c_corroborating.source_span],
        claims=[claim_c_corroborating],
        contradictions=[],
        hypotheses=[],
        run_id=run_c_id,
    )

    # Assert: 4 total historical records, but only 3 persistent deduplicated canonical claims!
    updated_counts = store.get_corpus_counts(run_id=run_c_id)
    assert updated_counts["historical_records"] == 4
    assert updated_counts["persistent_deduplicated"] == 3
    assert updated_counts["current_run_claims"] == 2

    # Verify source lineage was NOT deleted or overwritten
    conn = store._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM claim_sources WHERE canonical_fingerprint = ?", (claim_c.canonical_fingerprint,))
    sources_count = cursor.fetchone()[0]
    conn.close()
    assert sources_count == 2, "Source lineage must preserve multiple citations for the same canonical claim!"

    # -------------------------------------------------------------
    # 5. CRYPTOGRAPHIC SEQUENTIAL AUDIT CHAIN VERIFICATION
    # -------------------------------------------------------------
    audit_verification = store.verify_audit_chain()
    assert audit_verification["is_valid"] is True
    assert audit_verification["verified_events"] == 3
    assert audit_verification["breaks_detected"] == 0
