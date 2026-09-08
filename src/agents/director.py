"""
Research Director Agent.
Decomposes high-level objectives into targeted search queries and evaluates research gaps.
"""

from typing import List, Dict, Any
from src.agents.base import BaseAgent, AgentContext
from src.models.schemas import ToolPermission, ResearchObjective, ResearchGap
from src.gateway.base import ModelMessage


class ResearchDirectorAgent(BaseAgent):
    """Supervisor agent coordinating research objectives and query strategies."""

    name: str = "ResearchDirector"
    role: str = "Research Director & Strategy Orchestrator"
    description: str = "Decomposes research objectives into search queries and identifies missing variables."
    allowed_tools: List[str] = ["search_sources"]
    permission_level: ToolPermission = ToolPermission.READ_ONLY

    def run(self, context: AgentContext, objective: ResearchObjective, **kwargs) -> List[str]:
        """
        Formulate targeted queries from research objective with high-speed adaptation.
        """
        import re
        topic_clean = (objective.topic or "").strip()
        query_clean = (objective.query or "").strip()

        # Extract high-signal keywords from query and topic (skip conversational stop words)
        stop_words = {
            "and", "the", "for", "are", "etc", "like", "these", "is", "a", "an", "in", "on", "of", "to", "as",
            "into", "with", "from", "that", "this", "these", "those", "have", "has", "had", "more", "most",
            "about", "other", "their", "there", "they", "person", "newly", "starting", "getting", "field",
            "suffering", "rather", "than", "traditional", "online", "method", "methods", "how", "what",
            "when", "where", "which", "while", "get", "getting", "struggles"
        }
        query_words = [w for w in re.findall(r"\b[A-Za-z0-9_-]{3,}\b", query_clean) if w.lower() not in stop_words]
        topic_words = [w for w in re.findall(r"\b[A-Za-z0-9_-]{3,}\b", topic_clean) if w.lower() not in stop_words]
        
        core_query_kws = " ".join(query_words[:6]) if query_words else topic_clean
        core_topic_kws = " ".join(topic_words[:6]) if topic_words else (topic_clean or "Market Strategy")

        # Baseline robust targeted queries
        adaptive_queries = [
            core_query_kws,
            f"{core_topic_kws} empirical case studies playbooks strategies",
            f"{core_topic_kws} failure modes pitfalls risks",
            f"{core_topic_kws} economics metrics benchmarks",
        ]

        # Fast LLM enhancement with fallback
        try:
            prompt = (
                f"Topic: {core_topic_kws}\n"
                f"Query: {core_query_kws}\n"
                f"Generate 3 short, high-yield web search queries (under 7 words each). One query per line, no numbering."
            )
            response = self.model_gateway.generate(
                messages=[
                    ModelMessage(role="system", content="You are a research search query optimizer. Return 3 concise search engine queries, one per line."),
                    ModelMessage(role="user", content=prompt),
                ],
                task_class="FAST",
                max_tokens=150,
                correlation_id=context.correlation_id,
                actor_id=self.name,
            )
            if response and response.content:
                llm_lines = [re.sub(r'^\d+[\.\)]\s*|-\s*', '', line).strip(' "\'') for line in response.content.split('\n') if line.strip()]
                valid_queries = [l for l in llm_lines if len(l) > 5 and len(l) < 80]
                if valid_queries:
                    adaptive_queries = [core_query_kws] + valid_queries[:3]
        except Exception as e:
            logger.debug(f"Director fast query generation fallback: {e}")

        max_q = min(len(adaptive_queries), max(2, objective.max_depth + 1))
        return adaptive_queries[:max_q]

    def detect_research_gaps(
        self,
        context: AgentContext,
        objective: ResearchObjective,
        extracted_claims_count: int,
    ) -> List[ResearchGap]:
        """Identify missing evidence variables."""
        gaps = []
        if extracted_claims_count < 5:
            gaps.append(
                ResearchGap(
                    gap_id="GAP-0001",
                    topic=objective.topic,
                    description="Insufficient empirical trial evidence available in corpus.",
                    missing_variable="Empirical case study metrics on EBITDA returns",
                    suggested_query=f"{objective.topic} enterprise trial audited metrics",
                    priority=8.0,
                )
            )
        return gaps
