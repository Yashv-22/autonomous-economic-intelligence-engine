# Architectural Decision Records (ADRs)

**Author:** Principal AI Systems Architect & Senior Software Architect  
**Date:** September 2026  
**Status:** Canonical Architectural Decisions (Phase 0.5 Hardened & Audited)  

---

## ADR-001: Orchestration Architecture: Hierarchical Orchestrator-Worker with Shared Blackboard
*   **Decision:** Adopt the Hierarchical Orchestrator-Worker with Shared Blackboard pattern.
*   **Rationale:** Eliminates chaotic peer-to-peer message explosion, maintains centralized budget and recursion depth control, and enforces deterministic task dispatch.

---

## ADR-002: Universal Tool & Context Integration via Model Context Protocol (MCP)
*   **Decision:** Standardize all tool, resource, and prompt integrations on the Model Context Protocol (MCP) specification.
*   **Rationale:** Decouples model reasoning from tool implementations and enables plug-and-play reuse of enterprise connectors.

---

## ADR-003: Lean Storage Core in Phase 1 with Two-Stage Graph Evolution
*   **Decision:** Deploy PostgreSQL 16+ with `pgvector` (or SQLite + local vector indexing) in Phase 1. Defer Neo4j graph deployment to Phase 2, conditioned on a formal value benchmark.
*   **Rationale:** Avoids premature distributed database synchronization overhead before the incremental value of graph traversal is quantitatively proven.

---

## ADR-004: Out-of-Process Policy-as-Code (OPA) Defense-in-Depth
*   **Decision:** Enforce safety, decision rights, and resource limits via an external Open Policy Agent (OPA) / Rego engine within a 6-stage defense-in-depth pipeline.
*   **Rationale:** In-prompt system instructions are vulnerable to prompt injection. External policy evaluation provides a deterministic enforcement barrier at the Policy Decision Point (PDP).

---

## ADR-005: Local-First Core Architecture with LiteLLM Gateway
*   **Decision:** Build a Local-First Core orchestrated through LiteLLM Proxy, supporting seamless switching between local open-weight models (via vLLM/Ollama) and commercial cloud APIs.
*   **Rationale:** Eliminates vendor lock-in, enables confidential air-gapped testing, and lowers development costs.

---

## ADR-006: Staged Self-Improvement Scope (Levels 1–3 First)
*   **Decision:** Restrict self-improvement in early phases to Level 1 (Prompt Tuning), Level 2 (Workflow Re-routing), and Level 3 (Dynamic Tool Synthesis). Gated Level 4+ core code self-modification behind human approval.
*   **Rationale:** Eliminates the risk of catastrophic recursive codebase corruption.

---

## ADR-007: Mandatory 4-Tier Consequence/Reversibility Decision Matrix
*   **Decision:** Route all operational actions through a 4-Tier Decision Rights Matrix based on consequence severity and reversibility.
*   **Rationale:** Eliminates ambiguous accountability and prevents human review fatigue from turning safety checks into ceremonial rubber-stamping.

---

## ADR-008: Falsifiability of the Economic Routing Hypothesis ($\alpha$)
*   **Decision:** Formally define the falsification of the straight-through routing hypothesis ($\alpha$-dominance) as a first-class system success outcome.
*   **Rationale:** Prevents architectural confirmation bias; ensures the intelligence engine can report that exception management and workflow redesign dominate costs if supported by empirical data.

---

## ADR-009: Phase 0.5 Adversarial Audit as a Pre-Implementation Requirement
*   **Decision:** Establish a formal Phase 0.5 audit gate between architecture planning and implementation to stress-test claims, de-risk infrastructure, and establish a lean MVP-0.
*   **Rationale:** Ensures code implementation begins only on grounded, verified foundations.
