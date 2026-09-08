"""
Deterministic & Cryptographic Identifier Utilities.
"""

import hashlib
import uuid
from typing import Union


def generate_uuid() -> str:
    """Generate a standard UUID4 hex string."""
    return uuid.uuid4().hex


def generate_prefixed_id(prefix: str, counter: int = None, length: int = 4) -> str:
    """Generate a readable prefixed ID (e.g. CLAIM-0001 or DOC-a8b2c4)."""
    if counter is not None:
        return f"{prefix.upper()}-{counter:0{length}d}"
    return f"{prefix.upper()}-{uuid.uuid4().hex[:length*2].upper()}"


def compute_sha256(content: Union[bytes, str]) -> str:
    """Compute deterministic SHA-256 hex string."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def compute_content_hash(content: Union[bytes, str]) -> str:
    """Alias for compute_sha256."""
    return compute_sha256(content)
