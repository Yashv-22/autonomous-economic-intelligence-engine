# Implementation Roadmap: From MVP-0 to Enterprise Operating System

**Author:** Principal AI Systems Architect & Senior Software Architect  
**Date:** September 2026  
**Status:** Canonical Implementation Roadmap (Phase 0.5 Hardened & Audited)  

---

## 1. Executive Summary & Delivery Philosophy

To prevent premature architectural over-engineering, implementation proceeds through a **Disciplined 10-Phase Progression**. 

The initial milestone is **MVP-0 (Phase 1 Exit Gate)**, delivering a streamlined pipeline that ingests project documents and external papers, extracts structured claims, detects empirical contradictions, and formats a validated problem dossier for human review.

```
+===================================================================================+
| PHASE 0: Research, Analysis & Initial Blueprint (COMPLETE)                        |
+===================================================================================+
                                         │
                                         ▼
+===================================================================================+
| PHASE 0.5: Adversarial Audit & De-Risking (COMPLETE)                             |
+===================================================================================+
                                         │
                                         ▼
+===================================================================================+
| PHASE 1: Research Ingestion & Claim Extraction [MVP-0 GATE] (Weeks 1–3)           |
+===================================================================================+
                                         │
                                         ▼
+===================================================================================+
| PHASE 2: Knowledge Persistence & Graph Evaluation Gate (Weeks 4–6)                 |
+===================================================================================+
                                         │
                                         ▼
+===================================================================================+
| PHASE 3: Problem Discovery & Hypothesis Validation Engine [MVP-1] (Weeks 7–10)    |
+===================================================================================+
                                         │
                                         ▼
+===================================================================================+
| PHASES 4–10: Opportunity Engine, Solution Designer, Sandboxing, Scale             |
+===================================================================================+
```

---

## 2. Phase-by-Phase Specifications

### Phase 0: Research & Planning Blueprint
*   **Status:** **COMPLETE**
*   **Deliverables:** 11 canonical specification documents.

### Phase 0.5: Adversarial Audit & De-Risking
*   **Status:** **COMPLETE**
*   **Deliverables:** `phase-0.5-validation.md`, audited schemas, grounded claims, decoupled storage roadmap.

---

### Phase 1: Research Ingestion, Claim Extraction & MVP-0
*   **Duration:** Weeks 1–3 | **Complexity:** Lean (25 Points)
*   **Core Objective:** Build the foundational research ingestion and claim extraction pipeline, delivering **MVP-0**.
*   **Deliverables:**
    1.  Document Ingestion Engine (`src/ingestion/`): Ingests PDF, DOCX, and web text; generates SHA-256 paragraph-level hashes.
    2.  Claim Extraction Service (`src/extraction/`): Pydantic structured claim extraction using LiteLLM.
    3.  Contradiction Detector (`src/validation/`): Flags polar disagreements across extracted claims.
    4.  MVP-0 CLI Runner (`src/cli/`): Runs full pipeline over a test corpus and exports an audited Markdown/JSON problem dossier.
*   **Acceptance Criteria (MVP-0 Exit Gate):**
    *   Ingest 50 enterprise PDFs/DOCX files with 0 crashes.
    *   Extract structured claims with $100\%$ verifiable citation hash mappings.
    *   Detect at least 3 genuine cross-source contradictions (e.g., vendor productivity claim vs. independent analyst reality check).
*   **Anti-Goals:** Do NOT deploy Neo4j yet. Do NOT build autonomous coding agents.

---

### Phase 2: Knowledge Persistence & Graph Evaluation Gate
*   **Duration:** Weeks 4–6 | **Complexity:** Medium (35 Points)
*   **Core Objective:** Implement robust relational storage (PostgreSQL + `pgvector`) and execute a benchmark to determine whether Neo4j provides measurable value.
*   **Deliverables:**
    1.  PostgreSQL relational schema and vector index.
    2.  Graph benchmark evaluating recursive SQL CTEs vs. Neo4j Cypher on contradiction path traversal.
    3.  Conditional Neo4j deployment based on benchmark results.
*   **Exit Gate:** Graph database deployed only if benchmark demonstrates $\ge 25\%$ precision uplift or $5\times$ latency reduction.

---

### Phase 3: Autonomous Problem Discovery & Hypothesis Validation (MVP-1)
*   **Duration:** Weeks 7–10 | **Complexity:** High (50 Points)
*   **Core Objective:** Build the multi-agent diagnostic engine that detects value-stream friction patterns, generates formal hypotheses, and performs adversarial red-team validation.
*   **Deliverables:** Problem Discovery Agent, Hypothesis Formalizer, Adversarial Red-Team Validator.
*   **Exit Gate:** Autonomously identify at least 5 verified organizational pathologies with $\ge 90\%$ precision against ground truth.

---

### Phase 4 to Phase 10: Summary Progression
*   **Phase 4 (Weeks 11–13):** Opportunity Index ($I_{\text{opp}}$) & Econometric Sensitivity Engine.
*   **Phase 5 (Weeks 14–17):** Target Operating Model Designer & 4-Tier Decision Matrix Generator.
*   **Phase 6 (Weeks 18–22):** Sandboxed Prototype & Tool Coding Engine (Docker/gVisor).
*   **Phase 7 (Weeks 23–26):** Automated Evaluation, Telemetry & Continuous Benchmarking.
*   **Phase 8 (Weeks 27–31):** Controlled Self-Improvement (Levels 1–3: Prompts, Routing, Tools).
*   **Phase 9 (Weeks 32–38):** Autonomous Multi-Agent Shadow Deployment & Field Trials.
*   **Phase 10 (Weeks 39+):** Enterprise Production Operating System & Multi-Tenant Rollout.
