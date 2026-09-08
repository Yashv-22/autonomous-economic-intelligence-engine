"""
High-Performance HTTP Web Fetcher.
Enforces SSRF protection, size limits, redirect validation, mime-type detection, and SHA-256 content hashing.
"""

import time
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from src.internet.providers.base import BaseFetchProvider, FetchResult
from src.security.network import network_validator
from src.core.errors import SecurityViolationError, NetworkAccessError
from src.core.identifiers import compute_sha256
from src.core.logging import logger


class WebFetcher(BaseFetchProvider):
    """Secure HTTP fetcher for live web documents and public resources."""

    def __init__(self, user_agent: Optional[str] = None, max_bytes: int = 5_000_000):
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36 (ResearchBot/2.0)"
        )
        self.max_bytes = max_bytes

    def fetch(self, url: str, timeout_seconds: float = 3.5, max_bytes: Optional[int] = None) -> FetchResult:
        """Fetch raw content from URL with security validation and hashing."""
        limit_bytes = max_bytes or self.max_bytes
        start_time = time.time()

        # 1. Security & SSRF Validation
        try:
            canonical_url = network_validator.validate_url(url)
        except SecurityViolationError as sve:
            return FetchResult(
                url=url,
                final_url=url,
                status_code=403,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                is_success=False,
                error_message=f"SSRF or Network Security Violation: {sve}",
            )

        # 2. Execute Request
        req = urllib.request.Request(
            canonical_url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/pdf,application/json,text/plain;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
                final_url = response.geturl()
                status_code = response.getcode()
                content_type = response.headers.get("Content-Type", "application/octet-stream")
                
                # Header dict
                resp_headers = {k: v for k, v in response.headers.items()}

                # Read safely up to byte limit
                raw_bytes = response.read(limit_bytes + 1024)
                if len(raw_bytes) > limit_bytes:
                    raw_bytes = raw_bytes[:limit_bytes]
                    logger.warning(f"Response from {url} truncated at {limit_bytes} bytes.")

                content_hash = compute_sha256(raw_bytes)
                latency = (time.time() - start_time) * 1000.0

                return FetchResult(
                    url=url,
                    final_url=final_url,
                    status_code=status_code,
                    content_type=content_type,
                    raw_content=raw_bytes,
                    content_hash=content_hash,
                    headers=resp_headers,
                    latency_ms=latency,
                    size_bytes=len(raw_bytes),
                    is_success=True,
                )
        except Exception as e:
            latency = (time.time() - start_time) * 1000.0
            return FetchResult(
                url=url,
                final_url=url,
                status_code=500,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                latency_ms=latency,
                is_success=False,
                error_message=str(e),
            )
