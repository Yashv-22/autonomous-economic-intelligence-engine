"""
Minimum Viable Experiment Designer.
Calculates and synthesizes the cheapest, fastest experiments that can prove or disprove
an opportunity before committing engineering capital.
Enforces empirical cost baselines with explicit confidence labels and falsification kill criteria.
"""

from typing import List, Dict, Any, Optional
from src.opportunity.schemas import ValidationExperiment


class ExperimentDesigner:
    """
    Synthesizes ranked, low-cost falsification experiments for SaaS and automation opportunities.
    Every experiment defines: Cost, Time, Expected Information Gain, Success Criterion, and Kill Criterion.
    """

    @classmethod
    def design_experiments(
        cls,
        opportunity_id: str,
        opportunity_title: str,
        target_buyer_icp: str,
        core_value_proposition: str,
        problem_description: str,
    ) -> List[ValidationExperiment]:
        """Generate 4 ranked, progressively deeper falsification experiments."""

        exp1 = ValidationExperiment(
            experiment_id=f"EXP-{opportunity_id}-01",
            title=f"Target Buyer Problem & WTP Discovery Interviews ({target_buyer_icp})",
            tier="LEVEL_1_DISCOVERY",
            description=(
                f"Conduct 10 structured 20-minute discovery calls with active {target_buyer_icp} practitioners. "
                f"Probe current workaround workflows, monthly budget authority, and emotional pain regarding: '{problem_description[:100]}'."
            ),
            estimated_cost="$0 - $150 (Software / scheduling overhead)",
            cost_basis="Direct founder/researcher outreach via LinkedIn / email; zero external vendor cost",
            cost_confidence="HIGH",
            estimated_time="5 to 7 business days",
            expected_information_gain=0.88,
            success_criterion=">= 7 of 10 interviewees rate the problem >= 8/10 severity, and >= 4 state budget exists for external tooling.",
            kill_criterion=">= 6 of 10 interviewees report current internal spreadsheets or existing tools are 'good enough' to tolerate."
        )

        exp2 = ValidationExperiment(
            experiment_id=f"EXP-{opportunity_id}-02",
            title="Clickable Interactive Prototype & Paid Letter of Intent (LOI) Test",
            tier="LEVEL_2_COMMITMENT",
            description=(
                f"Assemble a Figma or lightweight clickable HTML prototype simulating '{opportunity_title}'. "
                f"Walk 5 vetted {target_buyer_icp} prospects through the workflow and present a non-binding early-adopter pilot agreement with defined pricing."
            ),
            estimated_cost="$100 - $350 (Domain, landing page hosting, mockup assets)",
            cost_basis="Low-code prototyping tools and prototype hosting; no backend code built",
            cost_confidence="HIGH",
            estimated_time="7 to 10 business days",
            expected_information_gain=0.92,
            success_criterion=">= 2 prospects sign a pilot LOI or agree to provide weekly sample data for an un-built prototype test.",
            kill_criterion="0 prospects agree to a follow-up review or all refuse to sign a pilot agreement citing lack of perceived ROI."
        )

        exp3 = ValidationExperiment(
            experiment_id=f"EXP-{opportunity_id}-03",
            title="Concierge Human-in-the-Loop Workflow Pilot",
            tier="LEVEL_3_CONCIERGE",
            description=(
                f"Offer a manual concierge service delivering '{core_value_proposition[:120]}' behind the scenes. "
                "The research team manually parses raw input files and returns reconciled outputs within 4 hours to simulate full automation."
            ),
            estimated_cost="$250 - $750 (Operator labor allocation & data sanitation tools)",
            cost_basis="Operator labor hours across 2 weeks of manual triage; avoids building automated microservices",
            cost_confidence="MEDIUM",
            estimated_time="10 to 14 business days",
            expected_information_gain=0.95,
            success_criterion="Customer uses the concierge service for >= 10 consecutive workflows and requests production SLA contract.",
            kill_criterion="Customer stops submitting workflow inputs after week 1, citing low urgency or excessive data preparation friction."
        )

        exp4 = ValidationExperiment(
            experiment_id=f"EXP-{opportunity_id}-04",
            title="Synthetic Enterprise Data Benchmark & Edge-Case Stress Test",
            tier="LEVEL_4_SYNTHETIC",
            description=(
                "Generate 10,000 synthetic enterprise transaction payloads simulating production schema drift, "
                "network packet latency, and concurrency anomalies to quantify failure rate boundaries."
            ),
            estimated_cost="$50 - $200 (Cloud compute and synthetic data scripts)",
            cost_basis="Cloud compute hours and local script execution",
            cost_confidence="HIGH",
            estimated_time="3 to 4 business days",
            expected_information_gain=0.78,
            success_criterion="Algorithmic pipeline maintains >= 99.2% straight-through accuracy with < 500ms latency under 5x volume spike.",
            kill_criterion="Error and exception rate exceeds 8% without manual intervention, proving algorithmic unreliability."
        )

        return [exp1, exp2, exp3, exp4]
