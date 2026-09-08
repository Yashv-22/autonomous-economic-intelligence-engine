"""
Fetch Tool implementation using WebFetcher.
"""

import urllib.parse
from typing import Dict, Any, Optional
from src.tools.base import BaseTool
from src.models.schemas import ToolPermission
from src.internet.fetcher.fetcher import WebFetcher
from src.core.identifiers import compute_sha256


class FetchTool(BaseTool):
    """Executes safe HTTP GET requests with SSRF guards and content hashing."""

    name: str = "fetch_web_content"
    description: str = "Fetches public HTML, PDF, or text content from a verified URL."
    permission_level: ToolPermission = ToolPermission.READ_ONLY
    requires_network: bool = True

    def __init__(self, fetcher: Optional[WebFetcher] = None, mock_web_index: Optional[Dict[str, str]] = None):
        super().__init__()
        self.fetcher = fetcher or WebFetcher()
        self.mock_web_index = mock_web_index or {}

    def run(self, url: str = "", timeout_seconds: int = 10, **kwargs) -> Any:
        """Fetch content from target URL."""
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc or url.split("//")[-1].split("/")[0].split("?")[0]

        if url in self.mock_web_index:
            html = self.mock_web_index[url]
            raw = html.encode("utf-8")
            h = compute_sha256(raw)
            return {
                "url": url,
                "final_url": url,
                "domain": domain,
                "status_code": 200,
                "content_type": "text/html",
                "content_hash": h,
                "document_hash": h,
                "size_bytes": len(raw),
                "latency_ms": 1.0,
                "text_preview": html[:500],
                "raw_html": html,
                "is_mock": True,
            }

        res = self.fetcher.fetch(url=url, timeout_seconds=timeout_seconds)
        if not res.is_success:
            raise RuntimeError(res.error_message or "Fetch failed.")

        final_parsed = urllib.parse.urlparse(res.final_url or url)
        final_domain = final_parsed.netloc or domain

        return {
            "url": res.url,
            "final_url": res.final_url,
            "domain": final_domain,
            "status_code": res.status_code,
            "content_type": res.content_type,
            "content_hash": res.content_hash,
            "document_hash": res.content_hash,
            "size_bytes": res.size_bytes,
            "latency_ms": res.latency_ms,
            "text_preview": res.raw_content[:500].decode("utf-8", errors="replace"),
            "raw_html": res.raw_content.decode("utf-8", errors="replace"),
            "is_mock": False,
        }
