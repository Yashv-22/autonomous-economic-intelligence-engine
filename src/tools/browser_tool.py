"""
Browser Navigation Tool implementation.
Exposes sandboxed browser navigation and action execution.
"""

from typing import Dict, Any, Optional
from src.tools.base import BaseTool
from src.models.schemas import ToolPermission
from src.internet.browser.crawl4ai_browser import Crawl4AIBrowserProvider


class BrowserTool(BaseTool):
    """Executes safe browser navigation and DOM inspection within an isolated sandbox."""

    name: str = "browser_navigate"
    description: str = (
        "Safely navigates an isolated headless browser to a web target, waits for dynamic "
        "selectors, and retrieves rendered content. Prohibits shell/subprocess execution."
    )
    permission_level: ToolPermission = ToolPermission.READ_ONLY
    requires_network: bool = True

    def __init__(self, browser_provider: Optional[Crawl4AIBrowserProvider] = None):
        super().__init__()
        self.browser = browser_provider or Crawl4AIBrowserProvider()

    def run(
        self,
        url: str = "",
        wait_for_selector: Optional[str] = None,
        timeout_seconds: float = 15.0,
        **kwargs,
    ) -> Any:
        """Navigate to webpage and return rendered DOM/Markdown."""
        if not url:
            raise ValueError("URL parameter is required for browser_navigate.")

        res = self.browser.navigate(
            url=url,
            wait_for_selector=wait_for_selector,
            timeout_seconds=timeout_seconds,
        )

        if not res.is_success:
            raise RuntimeError(res.error_message or f"Browser navigation failed for '{url}'.")

        return {
            "url": res.url,
            "final_url": res.final_url,
            "status_code": res.status_code,
            "content_hash": res.content_hash,
            "document_hash": res.content_hash,
            "markdown": res.markdown or res.raw_content.decode("utf-8", errors="replace"),
            "size_bytes": res.size_bytes,
            "latency_ms": res.latency_ms,
            "provider": res.acquisition_provider,
            "is_mock": res.is_mock,
            "evidence_status": res.evidence_status,
        }
