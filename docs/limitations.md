# Known Limitations & Boundaries

## 1. Current Architectural Boundaries

While the **Autonomous Economic Intelligence & Opportunity Engine** provides a robust, evidence-grounded research pipeline, users and developers should be aware of the following technical boundaries:

### 1.1 Model & Context Window Limits
* **Context Saturation:** When processing massive document corpora (hundreds of dense academic papers or 100+ page SEC filings), chunking and summarization strategies are required. Passing full texts directly to LLM context windows can lead to attention drift.
* **Extraction Hallucination Resilience:** While paragraph-level cryptographic SHA-256 provenance prevents false citations, models can occasionally misinterpret dense financial tables or ambiguous semantic phrasing.

### 1.2 Rate Limits & Provider Quotas
* **Public Model Gateways:** Direct calls to external frontier APIs (OpenAI, Gemini) are subject to external rate limits (RPM/TPM). When executing rapid bulk ingestion, requests may be throttled or queued.
* **Local Proxy Latency:** Local routing daemons (such as OmniRoute and FreeLLMAPI) depend on local host machine CPU/RAM or upstream provider connectivity.

### 1.3 Ingestion & Web Scraping Limits
* **JavaScript-Heavy Dynamic Pages:** Standard HTTP ingestion fetches static markup. Complex Single Page Applications (SPAs) or pages guarded by anti-bot verification (Cloudflare Turnstile, PerimeterX) require headless browser integration (e.g., Playwright or Jina Reader API).
* **PDF Layout Complexity:** Multi-column PDFs, embedded equations, and scanned bitmap images without OCR may experience reduced extraction fidelity compared to native text.

### 1.4 Knowledge Graph Scaling
* **Graph Storage:** The current implementation uses an in-memory `NetworkX` graph backed by a SQLite relational store (`intelligence_ledger.db`). While performant for thousands of nodes and claims, multi-million node enterprise knowledge graphs will benefit from specialized graph databases (e.g., Neo4j or Memgraph) in future milestones.

---

## 2. Status of Features: Implemented vs. Planned

| Feature Area | Current Status | Notes |
| :--- | :--- | :--- |
| **SHA-256 Provenance Ledger** | **Implemented** | Paragraph-level hashing and SQLite persistence. |
| **Claim Extraction & Schemas** | **Implemented** | Strongly typed Pydantic models with epistemic scoring. |
| **Contradiction Detection** | **Implemented** | Pairwise heuristic and LLM-assisted contradiction matching. |
| **Opportunity Discovery & TAM** | **Implemented** | Economic analysis, TAM/SAM/SOM, and margin modeling. |
| **Adversarial Validation** | **Implemented** | Threat modeling, platform risk, and fragility scoring. |
| **Unified Model Gateway** | **Implemented** | OmniRoute, FreeLLMAPI, Gemini, OpenAI, and Mock fallback. |
| **FastAPI Server & Web UI** | **Implemented** | Interactive visualization dashboard and REST API. |
| **Autonomous Research Director** | **Partially Implemented** | Proposes next research queries; fully autonomous query execution loop is being expanded. |
| **Learning Architecture / Meta-Eval**| **Partially Implemented** | Prototype heuristic weight updates based on research success signals. |
| **Distributed Multi-Node Sandboxing**| **Planned** | gVisor micro-containers across Kubernetes nodes. |
| **Enterprise Neo4j Graph Sync** | **Planned** | Real-time dual-write to enterprise property graph databases. |
