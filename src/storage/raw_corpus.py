"""
Raw Corpus Storage Manager.
Persists immutable, raw web and document artifacts in data/raw with full cryptographic provenance metadata.
"""

import os
import json
from typing import Optional, Dict, Any
from src.internet.providers.base import FetchResult
from src.core.identifiers import compute_sha256
from src.core.logging import logger


class RawCorpusManager:
    """Stores raw acquired bytes and metadata without modification."""

    def __init__(self, base_dir: str = "data/raw"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def store_raw_artifact(self, fetch_result: FetchResult, metadata_extra: Optional[Dict[str, Any]] = None) -> str:
        """
        Store raw bytes to disk keyed by content SHA-256 hash.
        Returns the absolute filepath of stored artifact.
        """
        content_hash = fetch_result.content_hash
        ext = ".html" if "html" in fetch_result.content_type.lower() else (
            ".pdf" if "pdf" in fetch_result.content_type.lower() else ".bin"
        )
        
        artifact_path = os.path.join(self.base_dir, f"{content_hash}{ext}")
        meta_path = os.path.join(self.base_dir, f"{content_hash}.meta.json")

        # Write binary content if not already present
        if not os.path.exists(artifact_path):
            with open(artifact_path, "wb") as f:
                f.write(fetch_result.raw_content)

        # Write metadata
        meta = {
            "url": fetch_result.url,
            "final_url": fetch_result.final_url,
            "content_hash": content_hash,
            "content_type": fetch_result.content_type,
            "status_code": fetch_result.status_code,
            "size_bytes": fetch_result.size_bytes,
            "fetched_at": fetch_result.fetched_at,
            "headers": fetch_result.headers,
            "extra": metadata_extra or {},
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        logger.info(f"RawCorpus: Persisted artifact {content_hash[:16]}... ({fetch_result.size_bytes} bytes)")
        return artifact_path

    def get_raw_artifact(self, content_hash: str) -> Optional[bytes]:
        """Retrieve raw bytes by content hash."""
        for filename in os.listdir(self.base_dir):
            if filename.startswith(content_hash) and not filename.endswith(".meta.json"):
                with open(os.path.join(self.base_dir, filename), "rb") as f:
                    return f.read()
        return None
