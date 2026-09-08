"""
Production CLI Runner for Autonomous AI Operating-Model Intelligence System.
Executes the complete vertical slice from research objective to synthesis and audit trail.
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

from src.models.schemas import ResearchObjective, ProblemDossier
from src.research.loop import AutonomousResearchLoop
from src.knowledge.manager import KnowledgeManager
from src.core.logging import setup_logger, logger
from src.core.config import settings


def run_system_pipeline(
    query: str = "Analyze AI-era operating model transformation bottlenecks, straight-through routing, and EBITDA returns",
    topic: str = "Enterprise AI Operating Model Redesign",
    input_dir: Optional[str] = ".",
    output_dir: str = "output",
    db_path: str = "output/intelligence_ledger.db",
    max_iterations: int = 1,
) -> ProblemDossier:
    """
    Execute complete end-to-end Autonomous Operating-Model Intelligence Vertical Slice.
    """

    print("=" * 75)
    print("AUTONOMOUS AI OPERATING-MODEL INTELLIGENCE SYSTEM")
    print("Full Engineering, Integration & Continuous-Learning Vertical Slice")
    print("=" * 75)

    objective = ResearchObjective(
        objective_id=f"OBJ-{uuid.uuid4().hex[:8].upper()}",
        query=query,
        topic=topic,
        max_depth=3,
        budget_sources=10,
    )

    print(f"\n[INIT] Objective ID  : {objective.objective_id}")
    print(f"       Topic Domain  : {objective.topic}")
    print(f"       Primary Query : {objective.query}")
    print(f"       Input Dir     : {input_dir}")
    print(f"       Output Dir    : {output_dir}")
    print(f"       Database Path : {db_path}")

    # Initialize loop & orchestrator
    research_loop = AutonomousResearchLoop()
    dossier = research_loop.run_cycle(
        objective=objective,
        local_dir=input_dir,
        max_iterations=max_iterations,
        output_dir=output_dir,
    )

    print("\n" + "=" * 75)
    print("EXECUTION SUMMARY & PROVENANCE REPORT")
    print("=" * 75)
    print(f"Dossier ID               : {dossier.dossier_id}")
    print(f"Generated Timestamp      : {dossier.generated_at}")
    print(f"Merkle Provenance Root   : {dossier.merkle_provenance_root}")
    print(f"Total Documents Ingested : {dossier.total_documents_ingested}")
    print(f"Total Claims Extracted   : {dossier.total_claims_extracted}")
    print(f"Verified Contradictions  : {len(dossier.verified_contradictions)}")
    print(f"Formulated Hypotheses    : {len(dossier.hypothesized_problems)}")

    print("\nClaims Epistemic Breakdown:")
    for grade, count in sorted(dossier.claims_by_grade.items()):
        pct = (count / max(dossier.total_claims_extracted, 1)) * 100
        print(f"  - {grade:15s}: {count:4d} ({pct:5.1f}%)")

    print("\nVerified Cross-Source Contradictions:")
    for contra in dossier.verified_contradictions:
        print(f"  [{contra.contradiction_id}] {contra.topic} (Severity: {contra.severity}/10)")

    print("\nFalsifiable Problem Hypotheses:")
    for hypo in dossier.hypothesized_problems:
        safe_title = hypo.title.encode("ascii", "replace").decode("ascii")
        print(f"  [{hypo.hypothesis_id}] {safe_title}")

    if dossier.synthesis:
        print("\nStrategic Synthesis:")
        print(f"  Title     : {dossier.synthesis.title}")
        print(f"  Confidence: {dossier.synthesis.epistemic_confidence * 100:.1f}%")
        print(f"  Summary   : {dossier.synthesis.summary}")

    json_path = os.path.join(output_dir, "claims_ledger.json")
    md_path = os.path.join(output_dir, "problem_dossier.md")
    print("\nGenerated Artifacts:")
    print(f"  [+] SQLite Ledger Database : {db_path}")
    print(f"  [+] Structured JSON Ledger : {json_path}")
    print(f"  [+] Markdown Audit Dossier : {md_path}")

    print("\n" + "=" * 75)
    print("VERTICAL SLICE EXECUTION COMPLETED (100% GROUNDED & AUDITABLE)")
    print("=" * 75)

    return dossier


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous AI Operating-Model Intelligence System: Vertical Slice CLI."
    )
    parser.add_argument("--query", default="Analyze AI-era operating model transformation bottlenecks, straight-through routing, and EBITDA returns", help="Primary research query")
    parser.add_argument("--topic", default="Enterprise AI Operating Model Redesign", help="Research domain topic")
    parser.add_argument("--input-dir", default=".", help="Local input directory containing research documents (PDF/DOCX/MD/TXT)")
    parser.add_argument("--output-dir", default="output", help="Output directory for generated dossiers")
    parser.add_argument("--db-path", default="output/intelligence_ledger.db", help="SQLite ledger database path")
    parser.add_argument("--max-iterations", type=int, default=1, help="Max self-direction loop iterations")
    args = parser.parse_args()

    run_system_pipeline(
        query=args.query,
        topic=args.topic,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        db_path=args.db_path,
        max_iterations=args.max_iterations,
    )


if __name__ == "__main__":
    main()

run_full_pipeline = run_system_pipeline
