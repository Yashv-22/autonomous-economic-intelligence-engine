"""
Render Dynamic Page Tool implementation.
Exposes client-side JavaScript execution and SPA DOM extraction via Crawl4AI.
"""

from typing import Dict, Any, Optional
from src.tools.base import BaseTool
from src.models.schemas import ToolPermission
from src.internet.providers.crawl4ai_provider import Crawl4AIProvider


class RenderDynamicPageTool(BaseTool):
    """Executes dynamic JavaScript in headless Chromium and captures fully rendered DOM."""

    name: str = "render_dynamic_page"
    description: str = (
        "Renders dynamic client-side JavaScript Single Page Applications (SPAs) and extracts "
        "the hydrated DOM / Markdown using Crawl4AI's headless browser engine."
    )
    permission_level: ToolPermission = ToolPermission.READ_ONLY
    requires_network: bool = True

    def __init__(self, crawler_provider: Optional[Crawl4AIProvider] = None):
        super().__init__()
        self.crawler = crawler_provider or Crawl4AIProvider()

    def run(
        self,
        url: str = "",
        js_code: Optional[str] = None,
        wait_for: Optional[str] = None,
        timeout_seconds: float = 20.0,
        **kwargs,
    ) -> Any:
        """Render page dynamically with optional JS evaluation."""
        if not url:
            raise ValueError("URL parameter is required for render_dynamic_page.")

        res = self.crawler.render_dynamic(
            url=url,
            js_code=js_code,
            wait_for=wait_for,
            timeout_seconds=timeout_seconds,
        )

        if not res.is_success:
            raise RuntimeError(res.error_message or f"Dynamic rendering failed for '{url}'.")

        return {
            "url": res.url,
            "final_url": res.final_url,
            "status_code": res.status_code,
            "content_type": res.content_type,
            "content_hash": res.content_hash,
            "document_hash": res.content_hash,
            "markdown": res.markdown or res.raw_content.decode("utf-8", errors="replace"),
            "size_bytes": res.size_bytes,
            "latency_ms": res.latency_ms,
            "executed_provider": res.acquisition_provider,
            "is_mock": res.is_mock,
            "evidence_status": res.evidence_status,
        }
