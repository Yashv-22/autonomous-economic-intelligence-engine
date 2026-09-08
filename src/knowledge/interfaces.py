"""
Knowledge Storage Interfaces and Abstractions.
Ensures pluggability across Relational, Semantic/Vector, and Graph storage layers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.models.schemas import (
    SourceSpan,
    ExtractedClaim,
    ContradictionRecord,
    ProblemHypothesis,
    AuditRecord,
    ProblemDossier,
)


class RelationalStoreInterface(ABC):
    """Interface for relational document, span, and claim persistence."""

    @abstractmethod
    def persist_all(
        self,
        spans: List[SourceSpan],
        claims: List[ExtractedClaim],
        contradictions: List[ContradictionRecord],
        hypotheses: List[ProblemHypothesis],
    ) -> None:
        """Persist all research artifacts atomically."""
        pass

    @abstractmethod
    def get_claims(self, entity_or_topic: Optional[str] = None) -> List[ExtractedClaim]:
        """Retrieve claims, optionally filtered by topic."""
        pass

    @abstractmethod
    def get_spans_by_document(self, document_name: str) -> List[SourceSpan]:
        """Retrieve all spans belonging to a document."""
        pass

    @abstractmethod
    def log_audit_record(self, record: AuditRecord) -> None:
        """Append an immutable audit entry."""
        pass

    @abstractmethod
    def get_audit_records(self, correlation_id: Optional[str] = None) -> List[AuditRecord]:
        """Retrieve audit history."""
        pass


class SemanticStoreInterface(ABC):
    """Interface for vector embedding indexing and similarity search."""

    @abstractmethod
    def index_item(self, item_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """Index a text item with metadata and compute embedding."""
        pass

    @abstractmethod
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search top_k nearest items by cosine similarity."""
        pass


class GraphStoreInterface(ABC):
    """Interface for knowledge graph and causal network relationships."""

    @abstractmethod
    def add_node(self, node_id: str, node_type: str, properties: Dict[str, Any]) -> None:
        """Add a graph entity node."""
        pass

    @abstractmethod
    def add_edge(self, source_id: str, target_id: str, relation_type: str, properties: Dict[str, Any] = None) -> None:
        """Add a directed relational edge."""
        pass

    @abstractmethod
    def get_neighbors(self, node_id: str, relation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve related neighbor nodes."""
        pass

    @abstractmethod
    def get_causal_path(self, start_id: str, end_id: str) -> List[str]:
        """Find causal path between two entities."""
        pass
