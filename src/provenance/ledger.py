"""
Cryptographic Source Provenance & Merkle Ledger Engine.
Maintains SHA-256 span verification, full lineage paths, and deterministic Merkle roots.
"""

import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from src.models.schemas import SourceSpan, ProvenanceMetadata
from src.core.identifiers import compute_sha256


class ProvenanceLedger:
    """Manages immutable cryptographic provenance and lineage for all research artifacts."""

    def __init__(self):
        self.span_registry: Dict[str, SourceSpan] = {}
        self.document_hashes: Dict[str, str] = {}
        self.metadata_registry: Dict[str, ProvenanceMetadata] = {}
        self.lineage_graph: Dict[str, List[str]] = {}  # artifact_id -> list of parent/child IDs

    def register_spans(self, spans: List[SourceSpan], metadata: Optional[ProvenanceMetadata] = None) -> str:
        """
        Register spans and optional document metadata, returning the Merkle root hash.
        """
        for span in spans:
            self.span_registry[span.span_hash] = span
            self.document_hashes[span.document_name] = span.document_hash

        if metadata:
            self.metadata_registry[metadata.document_hash] = metadata

        return self.compute_merkle_root()

    def record_lineage(self, parent_id: str, child_id: str):
        """Record causal/transformation lineage from parent artifact to derived artifact."""
        if parent_id not in self.lineage_graph:
            self.lineage_graph[parent_id] = []
        self.lineage_graph[parent_id].append(child_id)

    def verify_span(self, span_hash: str, text: str) -> bool:
        """Verify that text snippet matches its registered SHA-256 hash."""
        computed_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if computed_hash != span_hash:
            return False
        return span_hash in self.span_registry

    def compute_merkle_root(self) -> str:
        """Compute a deterministic Merkle-style root over all sorted span hashes."""
        if not self.span_registry:
            return hashlib.sha256(b"EMPTY_LEDGER").hexdigest()

        sorted_hashes = sorted(list(self.span_registry.keys()))
        current_layer = [h.encode("utf-8") for h in sorted_hashes]

        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                if i + 1 < len(current_layer):
                    combined = hashlib.sha256(current_layer[i] + current_layer[i + 1]).digest()
                else:
                    combined = hashlib.sha256(current_layer[i] + current_layer[i]).digest()
                next_layer.append(combined)
            current_layer = next_layer

        return hashlib.sha256(current_layer[0]).hexdigest()

    def get_summary(self) -> Dict[str, Any]:
        """Return ledger metadata summary."""
        return {
            "total_documents": len(self.document_hashes),
            "total_spans": len(self.span_registry),
            "merkle_root": self.compute_merkle_root(),
            "documents": self.document_hashes,
        }
