# Technical System Architecture: Autonomous AI Operating-Model Intelligence System

**Author:** Principal AI Systems Architect & Senior Software Architect  
**Date:** September 2026  
**Status:** Canonical Technical Architecture Blueprint (Phase 0.5 Hardened & Audited)  

---

## 1. System Vision & Architecture Philosophy

The **Autonomous AI Operating-Model Intelligence System** is an AI-native platform designed to investigate, model, diagnose, and solve organizational operating model failures in the AI era.

### 1.1 Architectural First Principles
1.  **Strict Control vs. Execution Separation:** The control plane (governance, policy, identity, kill switches) is out-of-process and decoupled from agent reasoning runtimes.
2.  **Epistemic Humility & Evidence Grounding:** The system treats every claim as an unverified hypothesis until corroborated by multi-source evidence graphs with temporal tracking.
3.  **Local-First, Pragmatic Evolution:** Phase 1 deploys a lean storage engine (PostgreSQL + `pgvector` or SQLite + local vector indexing). Advanced graph databases (Neo4j) are deployed conditionally based on empirical benchmarks.
4.  **Open Protocol Interoperability:** Tool execution and context exchange standardize on the **Model Context Protocol (MCP)** specification.

---

## 2. Subsystem Overview & Pragmatic Storage Evolution

```
+===================================================================================+
|               CONTROL & GOVERNANCE PLANE (IMMUTABLE SUPERVISOR)                   |
|  - Policy-as-Code Engine (OPA/Cedar)           - Emergency Kill Switch            |
|  - Ephemeral Identity & Non-Human IAM Broker   - 4-Tier Decision Rights Gate      |
|  - Immutably Logged Audit Trail (Append-Only)  - Resource & Budget Quota Governor |
+===================================================================================+
                                         │
                                         ▼
+===================================================================================+
|               ORCHESTRATION & RUNTIME PLANE (HYBRID BLACKBOARD)                   |
|   [ Research Director & Supervisor ] <──> [ Shared Blackboard State (Redis / DB) ]|
|         │                  │                      │                   │           |
|   [Domain Researchers] [Knowledge Eng.] [Problem Discovery] [Validation Agent]   |
+===================================================================================+
                                         │
            ┌────────────────────────────┼────────────────────────────┐
            ▼                            ▼                            ▼
+────────────────────────+  +────────────────────────+  +────────────────────────+
| PHASE 1: LEAN STORAGE  |  | MODEL ACCESS LAYER     |  | ISOLATED RUNTIME       |
| - PostgreSQL / SQLite  |  | - LiteLLM Router Proxy |  | - Isolated gVisor /    |
| - pgvector / Chroma    |  | - Frontier Models (API)|  |   Docker Sandbox Pods  |
| - Local Filesystem Blob|  | - Local Models (vLLM)  |  | - Network Allowlist GW |
+────────────────────────+  +────────────────────────+  +────────────────────────+
            │ (Experimental Gate: Phase 2)
            ▼
+────────────────────────+
| PHASE 2: GRAPH ENGINE  |
| - Neo4j / Kùzu Graph   |
| (If ≥25% gain proven)  |
+────────────────────────+
```

---

## 3. Storage Roadmap: Two-Stage Evolution

### Stage 1: Phase 1 Lean Core (Immediate Implementation)
*   **Relational Engine:** PostgreSQL 16+ (or SQLite for lightweight local runs) managing structured claims, problem records, sources, and audit logs.
*   **Vector Engine:** `pgvector` or local Chroma/FAISS managing dense embeddings for semantic search.
*   **Document Store:** Local filesystem storing raw PDFs, DOCX files, and cryptographic SHA-256 hashes.
*   *Advantage:* Eliminates 3-way distributed transaction synchronization and reduces workstation RAM footprint to $<2\text{GB}$.

### Stage 2: Phase 2 Graph Database Evaluation Gate
*   **Trigger Condition:** Deploy Neo4j or Kùzu **only if** a formal evaluation benchmark proves that graph path traversal achieves $\ge 25\%$ higher precision or $5\times$ lower latency than relational recursive queries (CTEs) in detecting multi-hop contradiction cycles.

---

## 4. The 6-Stage Security Defense-in-Depth Pipeline

Security is engineered across a 6-stage pipeline where every boundary is independently tested and defended:

```
[1. LLM Reasoning] ─── (Risk: Prompt Injection / Goal Hijacking)
       │                 └─> Defense: Text sanitization, stripped script tags, untrusted scratchpad.
       ▼
[2. Tool Request] ─── (Risk: Malformed Parameters / Schema Poisoning)
       │                 └─> Defense: Pydantic strict schema validation.
       ▼
[3. Policy Decision (OPA)] ── (Risk: Overly Permissive Rules / Logic Flaws)
       │                        └─> Defense: Deny-by-default, static policy unit tests.
       ▼
[4. Identity Broker] ─── (Risk: Credential Theft / Token Replay)
       │                    └─> Defense: Ephemeral JWTs with 60-second TTLs, subtask-bound.
       ▼
[5. Tool Execution] ─── (Risk: Sandbox Escape / Network Exfiltration)
       │                   └─> Defense: gVisor/Docker, read-only rootfs, tmpfs, --net=none.
       ▼
[6. External Database] ─── (Risk: Corrupted / Unauthorized State Mutation)
                           └─> Defense: Reverse-delta transaction log, instant 1-click rollback.
```

---

## 5. Local-First Execution vs. Enterprise Cloud Scaling

*   **Local-First Workstation:** Runs complete core engine in $<4\text{GB}$ RAM on a single developer machine with Python 3.12+, LiteLLM, PostgreSQL/SQLite, and local embeddings.
*   **Enterprise Scaling Abstraction:** Clean interface separation allows drop-in replacement with managed cloud services (AWS Aurora, Qdrant Cloud, Neo4j Aura, Kubernetes workers) when transaction volumes require distributed infrastructure.

---

## 6. Internet Capability Layer: Agent Reach Integration

The system incorporates **Agent Reach (v1.5.0)** as a modular capability provider within the existing `src/internet/providers/` abstraction:
*   **Search Routing (`AgentReachSearchProvider`):** Coordinates multi-channel research queries across Exa AI Semantic Web Search (via `mcporter`), GitHub repositories, Bilibili video indices, and V2EX developer topics, with automatic failover to DuckDuckGo.
*   **Content Fetching (`AgentReachFetchProvider`):** Dispatches target URLs to Jina Reader (`r.jina.ai`) for structured markdown extraction, `feedparser` for RSS/Atom syndication, and `yt-dlp` for video transcripts.
*   **Security & Provenance Integrity:** Untrusted Internet content is screened for prompt injections, protected against SSRF vulnerabilities via `network_validator`, and registered in the `ProvenanceLedger` with cryptographic SHA-256 Merkle hashes.

---

## 7. Model Gateway & Free-Tier Inference Infrastructure (FreeLLMAPI)

The inference subsystem is governed by a unified **Model Gateway** (`src/gateway/`) designed for multi-tier reliability, cost metering, and provider decoupling:
*   **Provider Abstraction (`BaseModelProvider`):** All agent invocation occurs through standardized `ModelMessage` and `ModelResponse` protocols. Direct provider implementations include `GeminiModelProvider` (Frontier), `OpenAIModelProvider` (Frontier), `FreeLLMAPIModelProvider` (Free-tier routing engine), and `MockModelProvider` (Deterministic offline baseline).
*   **FreeLLMAPI Infrastructure (`infrastructure/FreeLLMAPI/`):** Operates as a local OpenAI-compatible routing daemon on `http://127.0.0.1:3001/v1`. It multiplexes free-tier API quotas across 25+ model platforms (including Google Gemini free tier and Groq Llama 3.3) with declarative configurations, AES-GCM credential encryption, and zero-configuration unified API key discovery.
*   **Multi-Tier Fallback Chain:** The gateway implements an automated failover hierarchy:
    $$\text{Primary Provider (Gemini / OpenAI)} \longrightarrow \text{FreeLLMAPI (Free Model Pool)} \longrightarrow \text{Mock Provider}$$
    This architecture guarantees zero crashes during autonomous research loops even when upstream rate limits, quota exhaustions, or network partitions occur.
*   **Cost Accounting & Observability:** Automatically tracks token consumption and calculates USD costs (with FreeLLMAPI accounted at $0.00), emitting real-time `MODEL_GENERATION_COMPLETED` events onto the system `event_bus`.

