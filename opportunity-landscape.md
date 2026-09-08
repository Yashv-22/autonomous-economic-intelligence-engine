# Opportunity Landscape & Opportunity Scoring Engine

**Author:** Principal AI Systems Architect & Product Strategist  
**Date:** September 2026  
**Status:** Canonical Opportunity Framework & Catalog (Phase 0)  

---

## 1. Executive Summary

Transforming validated organizational problems into high-margin commercial and operational solutions requires an objective, mathematical scoring framework. Unstructured AI prioritization frequently falls victim to novelty bias, overvaluing technically complex but commercially marginal features while ignoring high-friction operational plumbing.

This document formalizes the **Opportunity Discovery Engine**, establishes the multi-attribute **Opportunity Index ($I_{\text{opp}}$)**, and analyzes the highest-leverage solution vectors for the enterprise operating model market.

---

## 2. Mathematical Opportunity Scoring Framework

Every potential solution or product capability is evaluated using a rigorous, multi-factor scoring algorithm:

$$I_{\text{opp}} = \frac{\left( W_E \cdot S_E + W_U \cdot S_U + W_A \cdot S_A + W_M \cdot S_M \right) \cdot \left( S_F \cdot S_D \right)}{1 + \lambda \cdot C_{\text{impl}} + \gamma \cdot R_{\text{gov}}}$$

Where:
*   **Value Drivers (Numerator):**
    *   $S_E$: **Economic Impact Score** ($0.0 - 10.0$) $\to$ Measurable EBITDA / unit cost impact.
    *   $S_U$: **Urgency & Frequency Score** ($0.0 - 10.0$) $\to$ How acute and frequent the pain point is.
    *   $S_A$: **Automation Potential Score** ($0.0 - 1.0$) $\to$ Percentage of workflow that can be executed straight-through.
    *   $S_M$: **Market Size & Willingness to Pay ($0.0 - 10.0$)** $\to$ Addressable TAM and budget availability.
    *   $S_F$: **Technical Feasibility Factor** ($0.0 - 1.0$) $\to$ Confidence in delivering production reliability today.
    *   $S_D$: **Defensibility / Moat Factor** ($0.0 - 1.0$) $\to$ Resistance to foundation model commoditization.
    *   $W_E, W_U, W_A, W_M$: Calibrated attribute weights ($W_E=0.35, W_U=0.25, W_A=0.20, W_M=0.20$).
*   **Friction Penalties (Denominator):**
    *   $C_{\text{impl}}$: **Implementation & Integration Complexity** ($1.0 - 10.0$).
    *   $R_{\text{gov}}$: **Regulatory & Governance Risk Exposure** ($1.0 - 10.0$).
    *   $\lambda, \gamma$: Scaling penalty coefficients ($\lambda=0.08, \gamma=0.05$).

### 2.1 The Prioritization Matrix

```
                          TECHNICAL FEASIBILITY & DEFENSIBILITY
                                Low                       High
                    +---------------------------+---------------------------+
               High |      STRATEGIC BETS       |     TIER 1: QUICK WINS    |
                    | High Economic Potential   |  High Economic Potential  |
                    | High Implementation Risk  |   High Feasibility & Moat |
E                   | (e.g., Full Autonomous    | (e.g., Cross-Functional   |
C                   |  Enterprise Agent Re-org) |  Schema & MCP Backbone)   |
O                   +---------------------------+---------------------------+
N                   |    DEPRIORITIZED TRAPS    |   TACTICAL ACCELERATORS   |
O               Low |  Low Economic Value       |  Low Economic Value       |
M                   |  High Implementation Risk |   Easy Implementation     |
I                   | (e.g., Autonomous Meeting | (e.g., Point Summarizers, |
C                   |  Transcribers & Chatbots) |  Internal Documentation)  |
                    +---------------------------+---------------------------+
```

---

## 3. Canonical Opportunity Record Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EnterpriseOpportunityRecord",
  "type": "object",
  "required": [
    "opportunity_id",
    "title",
    "addressed_problem_ids",
    "solution_archetype",
    "value_proposition",
    "target_customer_profile",
    "economic_impact_score",
    "automation_potential_score",
    "technical_feasibility_score",
    "defensibility_score",
    "implementation_complexity_score",
    "regulatory_risk_score",
    "opportunity_index",
    "moat_analysis",
    "pricing_and_unit_economics"
  ],
  "properties": {
    "opportunity_id": { "type": "string", "pattern": "^OPP-[0-9]{4}$" },
    "title": { "type": "string" },
    "addressed_problem_ids": { "type": "array", "items": { "type": "string" } },
    "solution_archetype": { 
      "type": "string", 
      "enum": ["ORCHESTRATION_MIDDLEWARE", "GOVERNANCE_WATCHDOG", "IDENTITY_BROKER", "DIAGNOSTIC_MINER", "HYBRID_SOLUTION"] 
    },
    "value_proposition": { "type": "string" },
    "target_customer_profile": { "type": "string" },
    "economic_impact_score": { "type": "number", "minimum": 0, "maximum": 10 },
    "urgency_score": { "type": "number", "minimum": 0, "maximum": 10 },
    "automation_potential_score": { "type": "number", "minimum": 0, "maximum": 1 },
    "technical_feasibility_score": { "type": "number", "minimum": 0, "maximum": 1 },
    "defensibility_score": { "type": "number", "minimum": 0, "maximum": 1 },
    "implementation_complexity_score": { "type": "number", "minimum": 1, "maximum": 10 },
    "regulatory_risk_score": { "type": "number", "minimum": 1, "maximum": 10 },
    "opportunity_index": { "type": "number" },
    "moat_analysis": { "type": "string" },
    "pricing_and_unit_economics": {
      "type": "object",
      "properties": {
        "pricing_model": { "type": "string" },
        "projected_acv_usd": { "type": "number" },
        "gross_margin_pct": { "type": "number" }
      }
    }
  }
}
```

---

## 4. Ranked Opportunity Catalog

### Opportunity Record: `OPP-0001` (Rank 1: Highest Leverage)
*   **Title:** Cross-Functional Execution Mesh & Schema Enforcement Backbone
*   **Addressed Problem IDs:** `["PROB-0001", "PROB-0002", "PROB-0004"]`
*   **Solution Archetype:** `ORCHESTRATION_MIDDLEWARE`
*   **Value Proposition:** An event-driven, Model Context Protocol (MCP) native middleware that translates outputs between disparate departmental systems (Engineering, GTM, Legal, Ops) via strict JSON schema contracts and automated semantic translation, eliminating swivel-chair friction and inter-silo latency.
*   **Target Customer:** Mid-to-Large Enterprises ($50M–$2B revenue) experiencing cross-functional friction after adopting localized AI point solutions.
*   **Parametric Scores:**
    *   $S_E = 9.5$, $S_U = 9.2$, $S_A = 0.88$, $S_M = 9.0$
    *   $S_F = 0.90$, $S_D = 0.92$ (Deep integration & data schema moat)
    *   $C_{\text{impl}} = 4.5$, $R_{\text{gov}} = 3.0$
    *   **Opportunity Index ($I_{\text{opp}}$):** **`5.24` (Rank #1)**
*   **Moat Analysis:** High switching costs; accumulating organizational metadata, custom MCP tool schemas, and event-history audit graphs creates an unassailable data flywheel that foundation models cannot replicate out-of-the-box.
*   **Pricing & Unit Economics:** Outcome-based SaaS + volume fee: $\$50\text{k} - \$250\text{k}$ ACV, $82\%$ gross margins.

---

### Opportunity Record: `OPP-0002` (Rank 2)
*   **Title:** Policy-as-Code Watchdog & Dynamic Decision Rights Governor
*   **Addressed Problem IDs:** `["PROB-0003", "PROB-0005"]`
*   **Solution Archetype:** `GOVERNANCE_WATCHDOG`
*   **Value Proposition:** An independent, runtime execution barrier that evaluates autonomous agent actions against Open Policy Agent (OPA) / Cedar declarative security policies and 4-tier decision rights matrices before mutation events reach enterprise databases.
*   **Target Customer:** Highly regulated enterprises (Financial Services, Healthcare, Insurance, Defense).
*   **Parametric Scores:**
    *   $S_E = 9.0$, $S_U = 9.5$, $S_A = 0.92$, $S_M = 8.5$
    *   $S_F = 0.92$, $S_D = 0.88$
    *   $C_{\text{impl}} = 4.0$, $R_{\text{gov}} = 2.5$
    *   **Opportunity Index ($I_{\text{opp}}$):** **`5.12` (Rank #2)**
*   **Moat Analysis:** Regulatory compliance certification (SOC2, ISO42001, HIPAA, EU AI Act), immutable audit logs, and pre-built industry policy packs.
*   **Pricing & Unit Economics:** Enterprise platform subscription: $\$80\text{k} - \$350\text{k}$ ACV, $88\%$ gross margins.

---

### Opportunity Record: `OPP-0003` (Rank 3)
*   **Title:** Automated Value-Stream Diagnostic & Bottleneck Miner
*   **Addressed Problem IDs:** `["PROB-0001", "PROB-0004"]`
*   **Solution Archetype:** `DIAGNOSTIC_MINER`
*   **Value Proposition:** A passive diagnostic engine that analyzes enterprise communication graphs, ticket transitions (Jira/ServiceNow), and system logs to identify upstream AI volume flooding, queue latency spikes, and un-redesigned workflow seams, generating an automated Operating Model Friction Blueprint.
*   **Target Customer:** Enterprise CIOs, COOs, and Transformation Advisory Consultancies.
*   **Parametric Scores:**
    *   $S_E = 8.5$, $S_U = 8.0$, $S_A = 0.80$, $S_M = 8.8$
    *   $S_F = 0.95$, $S_D = 0.80$
    *   $C_{\text{impl}} = 3.5$, $R_{\text{gov}} = 3.0$
    *   **Opportunity Index ($I_{\text{opp}}$):** **`4.68` (Rank #3)**
*   **Moat Analysis:** Proprietary value-stream diagnostic algorithms, benchmark database across anonymized cross-enterprise telemetry.
*   **Pricing & Unit Economics:** Diagnostic audit retainer / ongoing monitoring: $\$30\text{k} - \$120\text{k}$ per assessment.

---

### Opportunity Record: `OPP-0004` (Rank 4)
*   **Title:** Ephemeral Non-Human Identity & Scoped Tool Broker
*   **Addressed Problem IDs:** `["PROB-0005"]`
*   **Solution Archetype:** `IDENTITY_BROKER`
*   **Value Proposition:** Dynamic, task-scoped credential broker that mints sub-minute, least-privilege tokens for autonomous agents executing specific subtasks (e.g., read-only customer address lookup vs. write bank account modification), terminating credentials instantly upon subtask completion.
*   **Target Customer:** Cloud Security & IAM teams in enterprises deploying multi-agent swarms.
*   **Parametric Scores:**
    *   $S_E = 8.0$, $S_U = 8.8$, $S_A = 0.95$, $S_M = 8.0$
    *   $S_F = 0.88$, $S_D = 0.82$
    *   $C_{\text{impl}} = 4.8$, $R_{\text{gov}} = 2.0$
    *   **Opportunity Index ($I_{\text{opp}}$):** **`4.45` (Rank #4)**
*   **Moat Analysis:** Deep operating system, Kubernetes, and enterprise IAM (Okta, Microsoft Entra ID) integration hooks.
*   **Pricing & Unit Economics:** Per-agent / per-token authorization metering: $\$40\text{k} - \$180\text{k}$ ACV.
