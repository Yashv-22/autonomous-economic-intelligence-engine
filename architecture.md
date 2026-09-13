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

---

## 8. Web Intelligence Fabric (Phase 2 Upgrade)

The autonomous research loop is upgraded with a modular **Web Intelligence Fabric** (`src/internet/`) providing deep web investigation capabilities without modifying the authoritative core intelligence architecture:

### 8.1 Provider Abstraction & Contracts
*   **Normalized Protocols:** All web acquisition components adhere to standardized provider interfaces (`BaseSearchProvider`, `BaseFetchProvider`, `BaseCrawlerProvider`, `BaseMapProvider`, `BaseBrowserProvider` in `src/internet/providers/base.py`).
*   **Decoupled Capabilities:** High-level reasoning systems (Research Director, Investigation Planner, ToolRegistry) interact solely with capability contracts (`search`, `fetch`, `scrape`, `crawl`, `map`, `render_dynamic`, `browser_navigate`), isolating upstream engines from vendor-specific network APIs.

### 8.2 Capability Providers
*   **Firecrawl Provider (`src/internet/providers/firecrawl_provider.py`):** Interfaces with Firecrawl service via HTTP boundary to deliver high-fidelity Markdown scraping, recursive depth-controlled site crawling, and whole-domain URL topology mapping (`/v1/map`), protected by pre-dispatch SSRF validation and SHA-256 evidence hashing.
*   **Crawl4AI Provider (`src/internet/providers/crawl4ai_provider.py`):** Interfaces with Crawl4AI REST service boundary on port 11235 for dynamic JavaScript rendering, client-side SPA DOM hydration, and structured Markdown conversion without polluting the host environment with heavy browser dependencies.
*   **Agent Reach Provider (`src/internet/providers/agent_reach_provider.py`):** Handles platform syndication (YouTube transcript extraction, RSS/Atom feeds) and multi-channel discovery.
*   **Native Web Fetcher (`src/internet/fetcher/fetcher.py`):** High-speed, lightweight static HTTP acquisition with gzip decompression and connection pooling.

### 8.3 Adaptive Acquisition Router (`src/internet/acquisition/router.py`)
*   **Capability-Driven Routing:** Dynamically evaluates research requirements:
    *   *Static Known URL* $\rightarrow$ Native HTTP Fetcher.
    *   *Client-Side SPA / Dynamic JavaScript* $\rightarrow$ Crawl4AI (with Firecrawl fallback).
    *   *Explicit Page Scrape* $\rightarrow$ Firecrawl Scrape (with Crawl4AI fallback).
    *   *Domain Topology Discovery* $\rightarrow$ Firecrawl Map.
    *   *Deep Recursive Crawl* $\rightarrow$ Firecrawl Crawl.
    *   *Syndicated Feeds / Media* $\rightarrow$ Agent Reach.
*   **Truthful Lifecycle Tracking:** Audit records explicitly distinguish between `CONFIGURED`, `ELIGIBLE`, `SELECTED`, `ATTEMPTED`, `SUCCEEDED`, `FAILED`, and `FALLBACK`. Failed providers are never marked executed.
*   **Canonical Source Identity:** Cross-provider deduplication generates deterministic source identifiers (`SRC-<SHA256[:12]>`) based on normalized URL structure, preventing duplicate logical entities in the Knowledge Graph when multiple providers acquire the same target.
*   **Credential-Free Telemetry:** Detailed execution audits log latency, status codes, and provider lifecycles while strictly redacting sensitive tokens and API keys.

### 8.4 Security & Defensive Isolation
*   **SSRF Defense:** Mandatory pre-dispatch IP/scheme resolution (`src/security/network.py`) strictly forbids loopback (`127.0.0.1`, `localhost`), link-local (`169.254.169.254`), and RFC 1918 private subnets.
*   **Prompt Injection Containment:** External untrusted web text is sanitized via `ContentSanitizer`, defusing prompt injection markers (`[DEFUSED_INJECTION_MARKER: ...]`) before LLM ingestion.
*   **Mock / Fixture Isolation:** Offline fixtures carry unmistakable metadata (`evidence_status="TEST_FIXTURE"`, `is_mock=True`) and are strictly barred from entering production research runs or mutating persistent knowledge.
*   **Web Agent Standalone Boundary:** Audited `@firecrawl/agent-core` (`infrastructure/web-agent-main/`) was determined to feature unconstrained `bashExec` shell execution without OS sandbox support on Windows. In compliance with security directives, Web Agent remains strictly standalone and is prevented from executing unmonitored system calls.


