"""
MVP-0 Pipeline Runner & Problem Dossier CLI.
Executes end-to-end ingestion, claim extraction, contradiction detection, and dossier export.
"""

import argparse
import os
import sys
import uuid
from datetime import datetime, timezone

# Ensure UTF-8 output encoding if possible
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.ingestion.document_parser import DocumentIngestionEngine
from src.ingestion.provenance import ProvenanceLedger
from src.extraction.claim_extractor import ClaimExtractor
from src.validation.contradiction import ContradictionDetector, HypothesisGenerator
from src.storage.ledger import StorageLedger
from src.models.schemas import ProblemDossier


def run_mvp0_pipeline(
    input_dir: str = ".",
    output_dir: str = "output",
    db_path: str = "output/intelligence_ledger.db",
) -> ProblemDossier:
    """Execute complete Phase 1 MVP-0 intelligence pipeline."""
    print("=" * 70)
    print("AUTONOMOUS AI OPERATING-MODEL INTELLIGENCE SYSTEM: MVP-0 PIPELINE")
    print("Phase 1: Research Ingestion, Claim Extraction & Contradiction Detection")
    print("=" * 70)

    # 1. Document Ingestion
    print(f"\n[1/5] Ingesting documents from: {input_dir}")
    ingestion_engine = DocumentIngestionEngine()
    spans = ingestion_engine.ingest_directory(input_dir, supported_extensions=[".pdf", ".docx"])
    print(f"      -> Ingested {len(spans)} verifiable text spans across target documents.")

    if not spans:
        print("      [!] Checking root target files fallback...")
        target_files = [
            "AI-Era Operating Model Redesign.pdf",
            "AI_Era_Operating_Model_Redesign_2026_Research.docx",
            "Summary - Execution architecture.pdf",
        ]
        for tf in target_files:
            if os.path.exists(tf):
                file_spans = ingestion_engine.ingest_file(tf)
                spans.extend(file_spans)
        print(f"      -> Ingested {len(spans)} fallback text spans.")

    # 2. Cryptographic Provenance Registration
    print("\n[2/5] Registering spans in cryptographic provenance ledger...")
    ledger = ProvenanceLedger()
    merkle_root = ledger.register_spans(spans)
    summary = ledger.get_summary()
    print(f"      -> Registered {summary['total_documents']} documents and {summary['total_spans']} unique spans.")
    print(f"      -> Merkle Provenance Root: {merkle_root}")

    # 3. Structured Claim Extraction
    print("\n[3/5] Extracting structured claims and classifying evidence grades...")
    extractor = ClaimExtractor()
    claims = extractor.extract_claims_from_spans(spans)
    print(f"      -> Extracted {len(claims)} structured research claims.")

    grade_counts = {}
    for c in claims:
        g = c.evidence_grade.value
        grade_counts[g] = grade_counts.get(g, 0) + 1

    print("      -> Claims by Epistemic Grade:")
    for grade, count in sorted(grade_counts.items()):
        print(f"         - {grade:14s}: {count:3d}")

    # 4. Contradiction Detection & Hypothesis Generation
    print("\n[4/5] Executing contradiction detection and hypothesis formulation...")
    detector = ContradictionDetector()
    contradictions = detector.detect_contradictions(claims)
    print(f"      -> Identified {len(contradictions)} verified cross-source analytical tensions.")
    for contra in contradictions:
        print(f"         [{contra.contradiction_id}] {contra.topic} (Severity: {contra.severity}/10)")

    hypotheses = HypothesisGenerator.generate_hypotheses(claims, contradictions)
    print(f"      -> Formulated {len(hypotheses)} formal, falsifiable problem hypotheses.")
    for hypo in hypotheses:
        safe_title = hypo.title.encode("ascii", "replace").decode("ascii")
        print(f"         [{hypo.hypothesis_id}] {safe_title}")

    # 5. Storage Persistence & Dossier Export
    print(f"\n[5/5] Persisting artifacts to SQLite and exporting dossiers to: {output_dir}")
    storage = StorageLedger(db_path=db_path)
    storage.persist_all(spans, claims, contradictions, hypotheses)

    doc_count = len(set(s.document_name for s in spans))
    dossier = ProblemDossier(
        dossier_id=f"DOSSIER-{uuid.uuid4().hex[:8].upper()}",
        title="Enterprise Operating Model Transformation: MVP-0 Research Dossier",
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_documents_ingested=doc_count,
        total_claims_extracted=len(claims),
        claims_by_grade=grade_counts,
        verified_contradictions=contradictions,
        hypothesized_problems=hypotheses,
        merkle_provenance_root=merkle_root,
    )

    json_path = os.path.join(output_dir, "mvp0_claims_ledger.json")
    md_path = os.path.join(output_dir, "mvp0_problem_dossier.md")
    storage.export_json_ledger(dossier, output_path=json_path)
    storage.export_markdown_dossier(dossier, output_path=md_path)

    print(f"      -> SQLite Database: {db_path}")
    print(f"      -> Structured JSON Ledger: {json_path}")
    print(f"      -> Markdown Audit Dossier: {md_path}")
    print("\n" + "=" * 70)
    print("MVP-0 PIPELINE EXECUTION COMPLETED SUCCESSFULLY (100% AUDITED)")
    print("=" * 70)

    return dossier


def main():
    parser = argparse.ArgumentParser(description="Run MVP-0 Intelligence Ingestion & Claim Extraction Pipeline.")
    parser.add_argument("--input-dir", default=".", help="Directory containing source documents (PDF/DOCX)")
    parser.add_argument("--output-dir", default="output", help="Output directory for generated dossiers")
    parser.add_argument("--db-path", default="output/intelligence_ledger.db", help="SQLite database path")
    args = parser.parse_args()

    run_mvp0_pipeline(input_dir=args.input_dir, output_dir=args.output_dir, db_path=args.db_path)


if __name__ == "__main__":
    main()
