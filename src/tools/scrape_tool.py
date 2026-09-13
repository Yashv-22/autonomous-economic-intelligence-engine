"""
Scrape Page Tool implementation.
Exposes high-fidelity single-page web scraping via Firecrawl and Adaptive Router.
"""

from typing import Dict, Any, Optional
from src.tools.base import BaseTool
from src.models.schemas import ToolPermission
from src.internet.providers.firecrawl_provider import FirecrawlProvider
from src.internet.acquisition.router import AdaptiveAcquisitionRouter, AcquisitionRequirement


class ScrapeTool(BaseTool):
    """Executes high-fidelity page scraping with clean Markdown and structured metadata."""

    name: str = "scrape_page"
    description: str = (
        "Scrapes full-page content into clean Markdown and structured metadata using "
        "the Web Intelligence Fabric (Firecrawl / Crawl4AI). Respects SSRF boundaries."
    )
    permission_level: ToolPermission = ToolPermission.READ_ONLY
    requires_network: bool = True

    def __init__(
        self,
        firecrawl_provider: Optional[FirecrawlProvider] = None,
        router: Optional[AdaptiveAcquisitionRouter] = None,
    ):
        super().__init__()
        self.firecrawl = firecrawl_provider or FirecrawlProvider()
        self.router = router or AdaptiveAcquisitionRouter(firecrawl_provider=self.firecrawl)

    def run(self, url: str = "", formats: Optional[list] = None, timeout_seconds: float = 15.0, **kwargs) -> Any:
        """Scrape webpage and return normalized content dictionary."""
        if not url:
            raise ValueError("URL parameter is required for scrape_page.")

        req = AcquisitionRequirement(
            url=url,
            capability="scrape",
            timeout_seconds=timeout_seconds,
        )
        res, audit = self.router.route_acquisition(req)

        if not res.is_success:
            raise RuntimeError(res.error_message or f"Scraping failed for '{url}'.")

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
            "executed_provider": audit.executed_provider or res.acquisition_provider,
            "canonical_source_id": audit.source_id,
            "is_mock": res.is_mock,
            "evidence_status": res.evidence_status,
        }
