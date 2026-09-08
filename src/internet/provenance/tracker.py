"""
Internet Provenance Tracking Module.
Tags normalized internet content with cryptographic hashes and produces verifiable SourceSpan objects.
"""

from typing import List, Dict, Any, Optional
from src.models.schemas import SourceSpan
from src.ingestion.provenance import ProvenanceLedger
from src.internet.normalization.engine import NormalizedSourceDocument
from src.core.identifiers import compute_sha256
from src.core.logging import logger


class InternetProvenanceTracker:
    """
    Cryptographic provenance tracker for acquired internet sources.
    Transforms normalized documents into verifiable, Merkle-backed SourceSpan records.
    """

    def __init__(self, provenance_ledger: Optional[ProvenanceLedger] = None):
        self.ledger = provenance_ledger or ProvenanceLedger()

    def track_and_register(
        self,
        documents: List[NormalizedSourceDocument],
    ) -> List[SourceSpan]:
        """
        Convert normalized document chunks into SourceSpan objects and register in Merkle ledger.
        """
        all_spans: List[SourceSpan] = []

        for doc in documents:
            cursor = 0
            for idx, chunk in enumerate(doc.chunks):
                if not chunk.strip():
                    continue

                span_hash = compute_sha256(chunk)
                span = SourceSpan(
                    document_name=doc.title or doc.url,
                    document_hash=doc.content_hash,
                    page_or_section=f"chunk-{idx}",
                    paragraph_index=idx,
                    text=chunk,
                    span_hash=span_hash,
                    source_url=doc.url,
                    start_char=cursor,
                    end_char=cursor + len(chunk),
                )
                all_spans.append(span)
                cursor += len(chunk) + 2

        self.ledger.register_spans(all_spans)
        logger.info(
            f"InternetProvenanceTracker: Registered {len(all_spans)} spans across {len(documents)} documents. "
            f"Current Merkle Root: {self.ledger.compute_merkle_root()[:12]}..."
        )
        return all_spans
