import os
import json
import zipfile

output_dir = os.environ.get("DATASET_EXPORT_DIR")
if output_dir:
    os.makedirs(output_dir, exist_ok=True)

local_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "datasets")
os.makedirs(local_output_dir, exist_ok=True)

# 1. Research Planning Dataset
research_planning = [
    {
        "messages": [
            {"role": "system", "content": "You are the Research Director for an Autonomous AI Economic Intelligence System. Given a high-level research objective, decompose it into a structured research plan, required source types, and key investigation dimensions."},
            {"role": "user", "content": "Objective: Investigate why enterprise AI projects stall at the production handoff between data science teams and line-of-business compliance officers."},
            {"role": "assistant", "content": json.dumps({
                "objective": "Investigate enterprise AI production handoff stalls between data science and compliance.",
                "research_dimensions": [
                    "Cross-functional velocity drift and queue latency",
                    "Regulatory audit trail gaps in probabilistic model outputs",
                    "Swivel-chair human integration and manual middleware overhead"
                ],
                "source_types_required": [
                    "Enterprise case studies (Gartner, McKinsey QuantumBlack)",
                    "Regulatory compliance frameworks (EU AI Act, NIST AI Risk Management Framework)",
                    "Direct engineering post-mortems"
                ],
                "initial_queries": [
                    "enterprise ai deployment bottlenecks compliance handoff",
                    "mlops governance friction financial services 2025 2026"
                ],
                "stopping_criteria": "Saturation achieved when additional queries yield less than 5% novel graph entities or duplicate existing case studies."
            })}
        ]
    }
]

# 2. Claim Extraction Dataset
claim_extraction = [
    {
        "messages": [
            {"role": "system", "content": "You are the Epistemic Claims Extraction Engine. Extract discrete empirical claims from source text, classifying them by type, evidence grade, and confidence."},
            {"role": "user", "content": "Source Text: 'In our 2025 study across 40 Fortune 500 enterprises, automated agentic workflows reduced manual processing time by 65%, but 41% of workflows suffered from silent context decay over multi-step reasoning hops.'"},
            {"role": "assistant", "content": json.dumps({
                "claims": [
                    {
                        "claim_text": "Automated agentic workflows reduced manual processing time by 65% across 40 Fortune 500 enterprises in 2025.",
                        "claim_type": "ECONOMIC",
                        "evidence_grade": "STRONG_EMPIRICAL",
                        "confidence_score": 0.95,
                        "requires_verification": False
                    },
                    {
                        "claim_text": "41% of automated workflows suffered from silent context decay over multi-step reasoning hops.",
                        "claim_type": "TECHNICAL",
                        "evidence_grade": "STRONG_EMPIRICAL",
                        "confidence_score": 0.92,
                        "requires_verification": True
                    }
                ]
            })}
        ]
    }
]

# 3. Contradiction Analysis Dataset
contradiction_analysis = [
    {
        "messages": [
            {"role": "system", "content": "You are the Adversarial Contradiction Radar. Analyze conflicting sources, determine relationship status, reconcile hypotheses, and establish falsification criteria."},
            {"role": "user", "content": "Source A: 'Enterprise LLM deployments achieve 95% straight-through automation without human oversight.'\nSource B: 'Independent field audits show that 55% of enterprise LLM transactions require human escalation due to hallucination risks.'"},
            {"role": "assistant", "content": json.dumps({
                "contradiction_status": "DIRECT_CONTRADICTION",
                "discrepancy_analysis": "Source A reflects narrow synthetic sandbox benchmarks, whereas Source B reflects broad production telemetry across complex enterprise workflows.",
                "reconciliation_hypothesis": "Vendor benchmarks exclude unstructured exception handling and cross-system API latency.",
                "falsification_criteria": "To validate Source A, production logs from 20 independent companies must demonstrate >90% autonomy over 180 consecutive days without human intervention.",
                "recommended_action": "Discard Source A metrics for economic modeling; utilize Source B baseline."
            })}
        ]
    }
]

# 4. Opportunity Scoring Dataset
opportunity_scoring = [
    {
        "messages": [
            {"role": "system", "content": "You are the Opportunity Scorer. Evaluate operational friction and calculate the multi-attribute Opportunity Index I_opp."},
            {"role": "user", "content": "Problem: Manual verification of supplier compliance documents causes a 14-day procurement bottleneck for global manufacturing firms."},
            {"role": "assistant", "content": json.dumps({
                "opportunity_id": "OPP-0042",
                "title": "Autonomous Supply Chain Compliance & Policy Watchdog",
                "target_buyer": "Chief Procurement Officer / Head of Supply Chain",
                "economic_impact_e": 9.0,
                "urgency_u": 8.5,
                "willingness_to_pay_w": 8.0,
                "automation_potential_a": 0.85,
                "market_demand_m": 8.5,
                "feasibility_f": 0.90,
                "moat_d": 0.75,
                "complexity_c": 3.5,
                "governance_r": 2.0,
                "calculated_i_opp": 5.82,
                "rationale": "High economic waste in procurement verification combined with high automation potential yields top-tier opportunity score."
            })}
        ]
    }
]

# 5. Economic Reasoning Dataset
economic_reasoning = [
    {
        "messages": [
            {"role": "system", "content": "You are the Economic Intelligence Scorer. Compute financial pro-formas, ACV, payback periods, and label epistemic status."},
            {"role": "user", "content": "Client Profile: 5,000 employees, 3 hours spent weekly on manual document formatting, loaded labor cost $50/hour. Proposed automation handles 80% of formatting."},
            {"role": "assistant", "content": json.dumps({
                "calculation_breakdown": {
                    "annual_hours_wasted": 780000,
                    "gross_annual_waste_usd": 39000000,
                    "addressable_savings_80_percent": 31200000
                },
                "pricing_and_unit_economics": {
                    "recommended_annual_contract_value": 120000,
                    "estimated_payback_months": 2.1,
                    "ltv_cac_ratio": 9.5
                },
                "epistemic_status": "ESTIMATE_BASED_ON_CALCULATED_ASSUMPTIONS"
            })}
        ]
    }
]

# 6. Solution Design & TOM Dataset
solution_design = [
    {
        "messages": [
            {"role": "system", "content": "You are the Enterprise Solution Architect. Design target operating models and draft Model Context Protocol (MCP) JSON-RPC tool schemas."},
            {"role": "user", "content": "Design an MCP tool schema for querying enterprise ERP inventory levels securely."},
            {"role": "assistant", "content": json.dumps({
                "mcp_tool_schema": {
                    "name": "query_erp_inventory",
                    "description": "Securely query ERP stock levels with out-of-process OPA policy enforcement.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "sku_id": {"type": "string"},
                            "warehouse_region": {"type": "string"}
                        },
                        "required": ["sku_id", "warehouse_region"]
                    },
                    "security_guardrails": {
                        "ephemeral_nhi_required": True,
                        "opa_policy_gate": "allow_inventory_read"
                    }
                }
            })}
        ]
    }
]

# 7. Adversarial Red-Team Dataset
adversarial_redteam = [
    {
        "messages": [
            {"role": "system", "content": "You are the Adversarial Red-Team Agent. Stress-test proposed AI business opportunities and determine if they should be killed or proceed."},
            {"role": "user", "content": "Opportunity: AI-powered general brainstorming assistant for corporate retreat planning."},
            {"role": "assistant", "content": json.dumps({
                "evaluation_verdict": "KILL_OPPORTUNITY_NOW",
                "fatal_flaws": [
                    "Extremely low willingness-to-pay (discretionary HR budget)",
                    "Zero defensibility against native LLM chat interfaces (no moat)",
                    "Low recurrence and negligible workflow integration"
                ],
                "risk_score": 9.5,
                "recommendation": "Do not allocate engineering resources. Pivot immediately to high-frequency operational bottlenecks with strict compliance requirements."
            })}
        ]
    }
]

# 8. Research Director Dataset
research_director = [
    {
        "messages": [
            {"role": "system", "content": "You are the Research Director. Given current knowledge gaps, determine the next best investigation action."},
            {"role": "user", "content": "Current Knowledge: Demand = Strong (Score 9), Technical Feasibility = Strong (Score 8), Buyer Willingness-to-Pay = UNKNOWN."},
            {"role": "assistant", "content": json.dumps({
                "selected_action": "B. Conduct structured customer interviews with 15 target buyers (CFO/COO) to establish price elasticity and budget authority.",
                "expected_information_gain": 0.92,
                "economic_relevance": 0.95,
                "rationale": "Technical and demand risk are resolved; closing the WTP uncertainty is the highest-leverage path to validate unit economics."
            })}
        ]
    }
]

datasets = {
    "research_planning.jsonl": research_planning,
    "claim_extraction.jsonl": claim_extraction,
    "contradiction_analysis.jsonl": contradiction_analysis,
    "opportunity_scoring.jsonl": opportunity_scoring,
    "economic_reasoning.jsonl": economic_reasoning,
    "solution_design.jsonl": solution_design,
    "adversarial_redteam.jsonl": adversarial_redteam,
    "research_director.jsonl": research_director
}

for filename, data in datasets.items():
    # Session output dir
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    # Local workspace output dir
    local_filepath = os.path.join(local_output_dir, filename)
    with open(local_filepath, "w", encoding="utf-8") as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Write to external output_dir if specified
    if output_dir:
        external_filepath = os.path.join(output_dir, filename)
        with open(external_filepath, "w", encoding="utf-8") as f:
            for record in data:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

if output_dir:
    zip_path = os.path.join(output_dir, "research_llm_training_datasets.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename in datasets.keys():
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                zipf.write(filepath, arcname=filename)
    print(" - Session path:", zip_path)

local_zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "research_llm_training_datasets.zip")
with zipfile.ZipFile(local_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for filename in datasets.keys():
        filepath = os.path.join(local_output_dir, filename)
        if os.path.exists(filepath):
            zipf.write(filepath, arcname=filename)

print("Datasets created and zipped successfully at:")
print(" - Local workspace path:", local_zip_path)

