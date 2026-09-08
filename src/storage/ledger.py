"""
Relational Storage & Ledger Engine for Phase 1.
Implements SQLite persistence, JSON ledger export, and human-readable Markdown dossier generation.
"""

import json
import os
import sqlite3
import gc
from datetime import datetime, timezone
from typing import List, Dict
from src.models.schemas import (
    SourceSpan,
    ExtractedClaim,
    ContradictionRecord,
    ProblemHypothesis,
    ProblemDossier,
)


class StorageLedger:
    """Manages SQLite persistence and artifact export for Phase 1 MVP-0."""

    def __init__(self, db_path: str = "output/intelligence_ledger.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_name TEXT PRIMARY KEY,
                    document_hash TEXT NOT NULL,
                    total_spans INTEGER NOT NULL,
                    ingested_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spans (
                    span_hash TEXT PRIMARY KEY,
                    document_name TEXT NOT NULL,
                    page_or_section TEXT NOT NULL,
                    paragraph_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    FOREIGN KEY (document_name) REFERENCES documents(document_name)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS claims (
                    claim_id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    entity_or_topic TEXT NOT NULL,
                    evidence_grade TEXT NOT NULL,
                    institution TEXT,
                    quantitative_metric TEXT,
                    is_model_assumption INTEGER NOT NULL,
                    span_hash TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    tags TEXT,
                    FOREIGN KEY (span_hash) REFERENCES spans(span_hash)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contradictions (
                    contradiction_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    claim_a_id TEXT NOT NULL,
                    claim_b_id TEXT NOT NULL,
                    contradiction_type TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    severity REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hypotheses (
                    hypothesis_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    statement TEXT NOT NULL,
                    null_hypothesis TEXT NOT NULL,
                    falsification_criteria TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def persist_all(
        self,
        spans: List[SourceSpan],
        claims: List[ExtractedClaim],
        contradictions: List[ContradictionRecord],
        hypotheses: List[ProblemHypothesis],
    ):
        """Batch persist all parsed research artifacts to SQLite."""
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Insert documents
            doc_hashes = {}
            doc_span_counts = {}
            for s in spans:
                doc_hashes[s.document_name] = s.document_hash
                doc_span_counts[s.document_name] = doc_span_counts.get(s.document_name, 0) + 1

            for doc_name, doc_hash in doc_hashes.items():
                cursor.execute(
                    "INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?)",
                    (doc_name, doc_hash, doc_span_counts[doc_name], now),
                )

            # Insert spans
            for s in spans:
                cursor.execute(
                    "INSERT OR REPLACE INTO spans VALUES (?, ?, ?, ?, ?)",
                    (s.span_hash, s.document_name, s.page_or_section, s.paragraph_index, s.text),
                )

            # Insert claims
            for c in claims:
                cursor.execute(
                    "INSERT OR REPLACE INTO claims VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        c.claim_id,
                        c.text,
                        c.entity_or_topic,
                        c.evidence_grade.value,
                        c.institution,
                        c.quantitative_metric,
                        1 if c.is_model_assumption else 0,
                        c.source_span.span_hash,
                        c.confidence_score,
                        json.dumps(c.tags),
                    ),
                )

            # Insert contradictions
            for k in contradictions:
                cursor.execute(
                    "INSERT OR REPLACE INTO contradictions VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        k.contradiction_id,
                        k.topic,
                        k.claim_a.claim_id,
                        k.claim_b.claim_id,
                        k.contradiction_type.value,
                        k.explanation,
                        k.severity,
                    ),
                )

            # Insert hypotheses
            for h in hypotheses:
                cursor.execute(
                    "INSERT OR REPLACE INTO hypotheses VALUES (?, ?, ?, ?, ?)",
                    (h.hypothesis_id, h.title, h.statement, h.null_hypothesis, h.falsification_criteria),
                )

            conn.commit()
        finally:
            conn.close()

    def export_json_ledger(self, dossier: ProblemDossier, output_path: str = "output/mvp0_claims_ledger.json"):
        """Export the complete structured JSON ledger."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(dossier.model_dump_json(indent=2))

    def export_markdown_dossier(self, dossier: ProblemDossier, output_path: str = "output/mvp0_problem_dossier.md"):
        """Export a comprehensive human-auditable Markdown dossier."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        lines = [
            f"# MVP-0 Research & Problem Dossier: Operating Model Intelligence",
            f"",
            f"**Dossier ID:** `{dossier.dossier_id}`  ",
            f"**Generated:** {dossier.generated_at}  ",
            f"**Merkle Provenance Root:** `{dossier.merkle_provenance_root}`  ",
            f"",
            f"---",
            f"",
            f"## 1. Executive Ingestion & Extraction Summary",
            f"",
            f"- **Total Documents Ingested:** {dossier.total_documents_ingested}",
            f"- **Total Structured Claims Extracted:** {dossier.total_claims_extracted}",
            f"- **Verified Cross-Source Contradictions:** {len(dossier.verified_contradictions)}",
            f"- **Formulated Falsifiable Hypotheses:** {len(dossier.hypothesized_problems)}",
            f"",
            f"### Claims Breakdown by Epistemic Grade",
            f"| Epistemic Grade | Count | Percentage |",
            f"| :--- | :--- | :--- |",
        ]

        total = max(dossier.total_claims_extracted, 1)
        for grade, count in dossier.claims_by_grade.items():
            pct = (count / total) * 100
            lines.append(f"| `{grade}` | {count} | {pct:.1f}% |")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 2. Verified Cross-Source Analytical Contradictions",
            f"",
        ])

        for contra in dossier.verified_contradictions:
            lines.extend([
                f"### [{contra.contradiction_id}] {contra.topic}",
                f"**Type:** `{contra.contradiction_type.value}` | **Severity:** `{contra.severity}/10`  ",
                f"",
                f"> **Claim A [{contra.claim_a.claim_id}] ({contra.claim_a.institution or 'Source A'}):**",
                f"> \"{contra.claim_a.text}\"  ",
                f"> *Provenance:* [{contra.claim_a.source_span.document_name} ({contra.claim_a.source_span.page_or_section})](file:///{contra.claim_a.source_span.document_name}) | `SHA256: {contra.claim_a.source_span.span_hash[:12]}...`",
                f"",
                f"> **Claim B [{contra.claim_b.claim_id}] ({contra.claim_b.institution or 'Source B'}):**",
                f"> \"{contra.claim_b.text}\"  ",
                f"> *Provenance:* [{contra.claim_b.source_span.document_name} ({contra.claim_b.source_span.page_or_section})](file:///{contra.claim_b.source_span.document_name}) | `SHA256: {contra.claim_b.source_span.span_hash[:12]}...`",
                f"",
                f"**Analytical Synthesis:** {contra.explanation}",
                f"",
                f"---",
            ])

        lines.extend([
            f"",
            f"## 3. Formulated Falsifiable Problem Hypotheses",
            f"",
        ])

        for hypo in dossier.hypothesized_problems:
            lines.extend([
                f"### [{hypo.hypothesis_id}] {hypo.title}",
                f"**Formal Statement:** {hypo.statement}  ",
                f"",
                f"**Null Hypothesis ($H_0$):** `{hypo.null_hypothesis}`  ",
                f"",
                f"**Affected Functions:** {', '.join(hypo.affected_functions)}  ",
                f"",
                f"**Concrete Falsification Test:**",
                f"> {hypo.falsification_criteria}",
                f"",
                f"---",
            ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
