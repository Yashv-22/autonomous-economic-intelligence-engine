"""
Continuous Autonomous Research Acquisition Loop.
Executes iterative discovery, acquisition, gap resolution, and knowledge expansion with strict stopping criteria.
"""

from typing import Optional, List
from src.models.schemas import (
    ResearchObjective,
    ProblemDossier,
    ResearchGap,
)
from src.orchestration.orchestrator import HierarchicalOrchestrator
from src.research.gap_detector import ResearchGapDetector
from src.core.logging import logger


class AutonomousResearchLoop:
    """Manages iterative, self-directed research cycles with strict stopping budgets."""

    def __init__(self, orchestrator: Optional[HierarchicalOrchestrator] = None):
        self.orchestrator = orchestrator or HierarchicalOrchestrator()

    def run_cycle(
        self,
        objective: ResearchObjective,
        local_dir: Optional[str] = None,
        max_iterations: int = 2,
        output_dir: str = "output",
    ) -> ProblemDossier:
        """
        Execute iterative research loop until evidence threshold or max iterations reached.
        """
        from datetime import datetime
        run_id = getattr(objective, "run_id", None) or f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        objective.run_id = run_id

        logger.info(f"Starting Autonomous Research Loop [{run_id}] for objective: '{objective.query}' (Max Cycles: {max_iterations})")

        current_dossier: Optional[ProblemDossier] = None
        iteration = 1

        while iteration <= max_iterations:
            logger.info(f"--- Research Iteration {iteration}/{max_iterations} (Run: {run_id}) ---")

            # Execute full hierarchical workflow for current objective
            current_dossier = self.orchestrator.execute_research_workflow(
                objective=objective,
                local_dir=local_dir,
                output_dir=output_dir,
            )

            # Analyze evidentiary gaps for the isolated run
            claims = self.orchestrator.knowledge_manager.relational.get_claims(run_id=run_id)
            gaps = ResearchGapDetector.detect_gaps(objective, claims)

            if not gaps or iteration >= max_iterations:
                logger.info("Stopping criteria met: Evidence threshold satisfied or iteration budget exhausted.")
                break

            # Self-direction: Formulate next research query to target highest-priority gap
            top_gap = sorted(gaps, key=lambda g: g.priority, reverse=True)[0]
            logger.info(f"Self-Direction triggered by gap [{top_gap.gap_id}]: {top_gap.description}")
            logger.info(f"Generating follow-up query: '{top_gap.suggested_query}'")

            # Refine objective for next iteration with preserved run_id
            objective = ResearchObjective(
                objective_id=f"{objective.objective_id}-ITER{iteration}",
                run_id=run_id,
                query=top_gap.suggested_query,
                topic=top_gap.topic,
                max_depth=objective.max_depth,
                budget_sources=objective.budget_sources,
            )

            iteration += 1

        return current_dossier
