"""
Normalized Corpus Storage Manager.
Persists parsed, cleaned, span-decomposed documents in data/normalized with lineage links to raw corpus hashes.
"""

import os
import json
from typing import List, Optional, Dict, Any
from src.models.schemas import SourceSpan
from src.core.logging import logger


class NormalizedCorpusManager:
    """Stores structured, normalized text documents and span sequences."""

    def __init__(self, base_dir: str = "data/normalized"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def store_normalized_document(
        self,
        document_hash: str,
        document_name: str,
        source_url: Optional[str],
        spans: List[SourceSpan],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Persist normalized JSON representation of document and spans."""
        doc_path = os.path.join(self.base_dir, f"{document_hash}.json")
        payload = {
            "document_hash": document_hash,
            "document_name": document_name,
            "source_url": source_url,
            "total_spans": len(spans),
            "spans": [s.dict() for s in spans],
            "metadata": metadata or {},
        }
        with open(doc_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        logger.info(f"NormalizedCorpus: Persisted document {document_hash[:16]}... ({len(spans)} spans)")
        return doc_path

    def get_normalized_document(self, document_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve normalized document by hash."""
        doc_path = os.path.join(self.base_dir, f"{document_hash}.json")
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
