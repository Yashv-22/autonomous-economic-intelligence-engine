"""
Cryptographic Source Provenance & Tamper-Evident Ledger.
Maintains SHA-256 span verification and Merkle tree roots for ingested research.
"""

import hashlib
from typing import List, Dict
from src.models.schemas import SourceSpan


class ProvenanceLedger:
    """Manages immutable cryptographic provenance for all ingested research spans."""

    def __init__(self):
        self.span_registry: Dict[str, SourceSpan] = {}
        self.document_hashes: Dict[str, str] = {}

    def register_spans(self, spans: List[SourceSpan]) -> str:
        """Register a list of spans and return the master cryptographic Merkle root hash."""
        for span in spans:
            self.span_registry[span.span_hash] = span
            self.document_hashes[span.document_name] = span.document_hash

        return self.compute_merkle_root()

    def verify_span(self, span_hash: str, text: str) -> bool:
        """Verify that a given text snippet matches its registered SHA-256 hash."""
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

    def get_summary(self) -> Dict[str, any]:
        """Return ledger metadata summary."""
        return {
            "total_documents": len(self.document_hashes),
            "total_spans": len(self.span_registry),
            "merkle_root": self.compute_merkle_root(),
            "documents": self.document_hashes,
        }
