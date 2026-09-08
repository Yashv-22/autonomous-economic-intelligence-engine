"""
Persistent Research Memory & Session Store.
Preserves research context, query history, visited URLs, discovered entities, and gaps across process restarts.
"""

import os
import json
from typing import List, Set, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.core.identifiers import generate_prefixed_id
from src.core.logging import logger


class ResearchSessionState(BaseModel):
    session_id: str
    objective_id: str
    topic: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    executed_queries: List[str] = Field(default_factory=list)
    visited_urls: List[str] = Field(default_factory=list)
    discovered_entities: List[str] = Field(default_factory=list)
    discovered_concepts: List[str] = Field(default_factory=list)
    unexplored_areas: List[str] = Field(default_factory=list)
    research_gaps: List[str] = Field(default_factory=list)
    failed_searches: List[str] = Field(default_factory=list)
    total_spans_acquired: int = 0
    total_claims_extracted: int = 0
    is_saturated: bool = False
    saturation_reason: Optional[str] = None


class ResearchSessionStore:
    """Manages disk-persisted research sessions and checkpointing."""

    def __init__(self, base_dir: str = "data/sessions"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def create_or_load_session(self, topic: str, objective_id: Optional[str] = None) -> ResearchSessionState:
        """Create a new session or load an existing one matching the topic."""
        # Check existing sessions for topic
        for fname in os.listdir(self.base_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(self.base_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("topic", "").lower() == topic.lower():
                            logger.info(f"ResearchSession: Resuming existing session '{data['session_id']}' for topic '{topic}'")
                            return ResearchSessionState(**data)
                except Exception as e:
                    logger.warning(f"Error reading session file {fname}: {e}")

        # Create new session
        session_id = generate_prefixed_id("SESS")
        obj_id = objective_id or generate_prefixed_id("OBJ")
        state = ResearchSessionState(session_id=session_id, objective_id=obj_id, topic=topic)
        self.save_session(state)
        logger.info(f"ResearchSession: Initialized new persistent session '{session_id}'")
        return state

    def save_session(self, state: ResearchSessionState) -> None:
        """Save session state to disk checkpoint."""
        state.updated_at = datetime.now(timezone.utc).isoformat()
        fpath = os.path.join(self.base_dir, f"{state.session_id}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(state.dict(), f, indent=2)

    def record_query_execution(self, state: ResearchSessionState, query: str, results_count: int) -> None:
        """Record executed search query."""
        if query not in state.executed_queries:
            state.executed_queries.append(query)
        if results_count == 0 and query not in state.failed_searches:
            state.failed_searches.append(query)
        self.save_session(state)

    def record_visited_urls(self, state: ResearchSessionState, urls: List[str]) -> None:
        """Add URLs to visited registry."""
        for u in urls:
            norm_u = u.rstrip("/").lower()
            if norm_u not in state.visited_urls:
                state.visited_urls.append(norm_u)
        self.save_session(state)

    def record_knowledge_metrics(
        self,
        state: ResearchSessionState,
        new_spans_count: int,
        new_claims_count: int,
        new_entities: List[str],
        new_gaps: List[str],
    ) -> None:
        """Update knowledge counts and discovered entities."""
        state.total_spans_acquired += new_spans_count
        state.total_claims_extracted += new_claims_count
        for ent in new_entities:
            if ent not in state.discovered_entities:
                state.discovered_entities.append(ent)
        state.research_gaps = list(set(new_gaps))
        self.save_session(state)

    def list_sessions(self) -> List[ResearchSessionState]:
        """List all persisted research memory sessions."""
        if not os.path.exists(self.base_dir):
            return []
        sessions: List[ResearchSessionState] = []
        for fname in os.listdir(self.base_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(self.base_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        sessions.append(ResearchSessionState(**data))
                except Exception as e:
                    logger.warning(f"Could not load session file {fname}: {e}")
        return sessions

