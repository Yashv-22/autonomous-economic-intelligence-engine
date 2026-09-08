# Agent Specification & Role Taxonomy: Multi-Agent Operating System

**Author:** Principal AI Systems Architect & Senior Software Architect  
**Date:** September 2026  
**Status:** Canonical Agent Specification Blueprint (Phase 0)  

---

## 1. Executive Summary

The **Autonomous AI Operating-Model Intelligence System** utilizes a **Hierarchical Orchestrator-Worker with Shared Blackboard** architecture. Rather than permitting unconstrained peer-to-peer agent chatter—which empirically leads to context fragmentation, looping, and state divergence—all agent tasks are explicitly dispatched, monitored, validated, and recorded through structured contracts.

This document defines the formal specifications for all 12 specialized agent roles in the estate, including capabilities, toolsets, input/output schemas, trust boundaries, and failure mitigations.

---

## 2. The Agent Hierarchy & Interaction Architecture

```
                               ┌────────────────────────────────┐
                               │  RESEARCH DIRECTOR & SUPERVISOR │
                               └────────────────┬───────────────┘
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 ▼                              ▼                              ▼
  ┌──────────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────────────┐
  │      RESEARCH DIVISION       │ │   INTELLIGENCE DIVISION  │ │     SYNTHESIS & BUILD        │
  │ ├── Strategy Researcher      │ │ ├── Knowledge Engineer   │ │ ├── Opportunity Scorer       │
  │ ├── Tech/AI Researcher       │ │ ├── Problem Discoverer   │ │ ├── Solution Architect       │
  │ └── Academic Literature Rsch │ │ ├── Hypothesis Agent     │ │ ├── Coding Agent             │
  │                              │ │ └── Validation Agent     │ │ └── Watchdog Evaluator       │
  └──────────────────────────────┘ └──────────────────────────┘ └──────────────────────────────┘
                 │                              │                              │
                 └──────────────────────────────┴──────────────────────────────┘
                                                │
                                                ▼
                               ┌────────────────────────────────┐
                               │ SHARED BLACKBOARD & GRAPH DB   │
                               │ (PostgreSQL, Qdrant, Neo4j)    │
                               └────────────────────────────────┘
```

---

## 3. Comprehensive Agent Role Specifications

### 3.1 Research Director & Supervisor Agent
*   **Role ID:** `AGENT-DIR-001`
*   **Core Objective:** High-level strategic planning, task decomposition, worker delegation, progress monitoring, budget tracking, and human-in-the-loop escalation.
*   **Trust Boundary:** Tier II (Bounded Autonomous Orchestration). Cannot modify system security policies or deploy untested code.
*   **Permitted MCP Tools:**
    *   `mcp-supervisor:dispatch_task(agent_id, task_payload)`
    *   `mcp-supervisor:read_blackboard_state(query)`
    *   `mcp-supervisor:escalate_to_human(alert_level, reason, context)`
    *   `mcp-supervisor:terminate_agent_task(task_id)`
*   **Input Schema:** User research directive or automated diagnostic trigger.
*   **Output Schema:** Structured Master Execution Plan & Aggregated Executive Reports.
*   **Failure Modes & Containment:**
    *   *Failure:* Endless delegation loops or hallucinated task completion.
    *   *Containment:* Max recursion depth limit ($D_{\text{max}} = 5$), execution timeout, and budget tripwires enforced by the immutable control plane.

---

### 3.2 Strategy & Operating Model Researcher
*   **Role ID:** `AGENT-RSCH-002`
*   **Core Objective:** Extract, analyze, and synthesize organizational transformation research from strategy consulting firms (McKinsey, BCG, Bain, Deloitte, PwC).
*   **Trust Boundary:** Tier I (Read-Only Search & Extraction).
*   **Permitted MCP Tools:**
    *   `mcp-web:search_consulting_repositories(query, domain_filter)`
    *   `mcp-web:fetch_and_parse_pdf(url_or_filepath)`
    *   `mcp-knowledge:submit_extracted_claims(claims_array)`
*   **Input Schema:** Specific research queries (e.g., "Analyze organizational handoff bottlenecks in claims underwriting").
*   **Output Schema:** Normalized array of strategic claims with institutional source provenance and evidence tags (`[FACT]`, `[EVIDENCE]`, `[INFERENCE]`).
*   **Failure Modes & Containment:** Hallucinated citations. Contained via deterministic URL verification and PDF text-span hashing.

---

### 3.3 Technology & AI Architecture Researcher
*   **Role ID:** `AGENT-RSCH-003`
*   **Core Objective:** Monitor, extract, and evaluate emerging AI agent frameworks, Model Context Protocol (MCP) developments, runtime platforms, and enterprise tooling architectures.
*   **Trust Boundary:** Tier I (Read-Only Search & Architecture Extraction).
*   **Permitted MCP Tools:**
    *   `mcp-web:search_tech_blogs_and_docs(query, tech_filter)`
    *   `mcp-github:inspect_open_source_repo(repo_url, path)`
    *   `mcp-knowledge:submit_tech_capabilities(capability_record)`
*   **Input Schema:** Technology evaluation directives (e.g., "Assess stateful vs. stateless MCP 2026 specs").
*   **Output Schema:** Technical Architecture Capability Matrix with readiness scores and integration dependencies.

---

### 3.4 Academic & Empirical Literature Researcher
*   **Role ID:** `AGENT-RSCH-004`
*   **Core Objective:** Query peer-reviewed academic databases (ArXiv, PubMed, Semantic Scholar, SSRN, Stanford HAI) to identify empirical studies on human-computer interaction, organizational science, and multi-agent coordination.
*   **Trust Boundary:** Tier I (Read-Only Academic Search).
*   **Permitted MCP Tools:**
    *   `mcp-arxiv:search_papers(query, category, date_range)`
    *   `mcp-semantic-scholar:get_paper_citations(doi_or_id)`
    *   `mcp-knowledge:submit_academic_findings(paper_summary)`
*   **Input Schema:** Theoretical and empirical research questions.
*   **Output Schema:** Academic Evidence Dossier with peer-review status, methodology classification, sample size, and statistical confidence intervals.

---

### 3.5 Knowledge Engineer & Graph Architect
*   **Role ID:** `AGENT-KNOW-005`
*   **Core Objective:** Transform unstructured claims and research outputs into structured entity-relationship triples, update the Neo4j Knowledge Graph, generate dense vector embeddings, and resolve cross-source entity duplicates.
*   **Trust Boundary:** Tier II (Knowledge Graph Mutation).
*   **Permitted MCP Tools:**
    *   `mcp-graph:upsert_entity_node(entity_type, properties)`
    *   `mcp-graph:create_relationship(from_node, rel_type, to_node, properties)`
    *   `mcp-graph:detect_contradiction_cycles(entity_id)`
    *   `mcp-vector:upsert_embeddings(document_chunk, metadata)`
*   **Input Schema:** Raw research extraction payloads from research agents.
*   **Output Schema:** Validated graph transaction hashes and updated entity node IDs.

---

### 3.6 Problem Discovery & Pattern Recognition Agent
*   **Role ID:** `AGENT-DISC-006`
*   **Core Objective:** Continuously traverse the knowledge graph to cluster operational friction signals, detect cross-functional drift patterns, and instantiate candidate Problem Records.
*   **Trust Boundary:** Tier II (Problem Record Generation).
*   **Permitted MCP Tools:**
    *   `mcp-graph:run_graph_clustering(algorithm, parameters)`
    *   `mcp-problem:instantiate_problem_record(problem_draft_payload)`
*   **Input Schema:** Periodic graph state triggers or targeted value-stream queries.
*   **Output Schema:** Draft `OrganizationalProblemRecord` adhering to the canonical schema.

---

### 3.7 Hypothesis Generation & Formalizer Agent
*   **Role ID:** `AGENT-HYPO-007`
*   **Core Objective:** Convert loose problem descriptions into mathematically and operationally formal hypotheses with falsifiable predictions and required validation conditions.
*   **Trust Boundary:** Tier I (Analytical Inference).
*   **Permitted MCP Tools:**
    *   `mcp-knowledge:query_semantic_context(concept)`
    *   `mcp-hypothesis:publish_formal_hypothesis(hypothesis_payload)`
*   **Input Schema:** Candidate Problem Record.
*   **Output Schema:** Falsifiable Hypothesis Record with null hypothesis ($H_0$), alternative hypothesis ($H_1$), required test variables, and boundary conditions.

---

### 3.8 Evidence Validation & Contradiction Agent
*   **Role ID:** `AGENT-VAL-008`
*   **Core Objective:** Act as an adversarial "Red Team" against proposed hypotheses: actively searching for counter-evidence, disproving false claims, evaluating sample bias, and computing Bayesian confidence scores.
*   **Trust Boundary:** Tier I (Adversarial Search & Validation Scoring).
*   **Permitted MCP Tools:**
    *   `mcp-web:search_counter_evidence(claim_statement)`
    *   `mcp-graph:check_cross_source_corroboration(claim_id)`
    *   `mcp-validation:update_problem_confidence(problem_id, confidence_score, audit_log)`
*   **Input Schema:** Hypothesis Record & Problem Record.
*   **Output Schema:** Validation Verdict (`EMPIRICALLY_PROVEN`, `PARTIALLY_VALIDATED`, `DISPROVED`) with multi-source evidence provenance.

---

### 3.9 Opportunity Analysis & Econometric Scorer
*   **Role ID:** `AGENT-OPP-009`
*   **Core Objective:** Execute the mathematical Opportunity Index calculation ($I_{\text{opp}}$), perform P&L sensitivity modeling, evaluate moat defensibility, and rank solution priorities.
*   **Trust Boundary:** Tier II (Opportunity Ranking).
*   **Permitted MCP Tools:**
    *   `mcp-calculator:compute_opportunity_index(scoring_params)`
    *   `mcp-opportunity:publish_opportunity_record(opportunity_payload)`
*   **Input Schema:** Validated Problem Record and industry financial parameters.
*   **Output Schema:** Scored and ranked `EnterpriseOpportunityRecord`.

---

### 3.10 Solution Architect & Operating Pod Designer
*   **Role ID:** `AGENT-ARCH-010`
*   **Core Objective:** Design concrete target-state architectures: decomposing workflows into event-driven task graphs, assigning 4-Tier decision rights, designing MCP tool contracts, and defining Human-Agent Pod compositions.
*   **Trust Boundary:** Tier II (System Design Synthesis).
*   **Permitted MCP Tools:**
    *   `mcp-design:generate_task_graph(workflow_definition)`
    *   `mcp-design:assign_decision_tiers(decision_points_array)`
    *   `mcp-design:export_mcp_connector_spec(tool_spec_json)`
*   **Input Schema:** Scored Opportunity Record.
*   **Output Schema:** Formal Target Operating Model (TOM) Blueprint & Tool Specification Artifacts.

---

### 3.11 Prototype & Tool Coding Agent
*   **Role ID:** `AGENT-CODE-011`
*   **Core Objective:** Generate clean, typed, modular code for MCP connectors, event orchestration pipelines, and data schema validators in sandboxed environments.
*   **Trust Boundary:** Tier II (Sandboxed Code Synthesis). Strict prohibition against touching production systems or modifying control plane policies.
*   **Permitted MCP Tools:**
    *   `mcp-sandbox:write_code_file(filepath, content)`
    *   `mcp-sandbox:run_isolated_tests(test_command)`
    *   `mcp-sandbox:run_linter_and_typecheck(options)`
*   **Input Schema:** Tool Specification and Architecture Contract.
*   **Output Schema:** Validated, linted, unit-tested code repository in the sandbox directory.

---

### 3.12 Watchdog Evaluator & Policy Enforcement Agent
*   **Role ID:** `AGENT-WATCH-012`
*   **Core Objective:** Perform independent runtime safety checks: verifying that all agent outputs conform to Open Policy Agent (OPA) rules, JSON schemas, budget constraints, and ethical guardrails before any mutation is executed.
*   **Trust Boundary:** Tier III (Immutable Enforcement Barrier). Operates with independent process isolation and cannot be overridden by other agents.
*   **Permitted MCP Tools:**
    *   `mcp-policy:evaluate_opa_policy(policy_bundle, action_payload)`
    *   `mcp-policy:verify_json_schema(schema, data)`
    *   `mcp-policy:issue_execution_permit(action_id)`
    *   `mcp-policy:trigger_security_veto(reason, payload)`
*   **Input Schema:** All inter-agent and external mutation requests.
*   **Output Schema:** Cryptographic Permit Signature or Security Veto Alert.

---

## 4. Inter-Agent Communication Protocols

1.  **Strict Serialization via Typed JSON:** Natural language dialogue between agents is strictly disallowed for operational actions. Agents communicate exclusively via typed JSON payloads conforming to versioned schemas.
2.  **Shared Blackboard State:** Task state and knowledge updates are committed directly to Redis and PostgreSQL. Agents poll/subscribe to explicit event queues rather than retaining hidden local state.
3.  **Adversarial Separation of Concerns:** Research and synthesis agents cannot validate their own findings; validation is mandatory and executed exclusively by independent red-team agents (`AGENT-VAL-008` and `AGENT-WATCH-012`).
