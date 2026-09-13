"""
Site Map Tool implementation.
Exposes domain topology and URL discovery via Firecrawl Map capability.
"""

from typing import Dict, Any, List, Optional
from src.tools.base import BaseTool
from src.models.schemas import ToolPermission
from src.internet.providers.firecrawl_provider import FirecrawlProvider


class MapSiteTool(BaseTool):
    """Discovers all subpages, sitemap entries, and topology links for a target domain."""

    name: str = "map_site"
    description: str = (
        "Maps the topology of a website and discovers all internal links and sitemap URLs "
        "using Firecrawl's site mapping engine."
    )
    permission_level: ToolPermission = ToolPermission.READ_ONLY
    requires_network: bool = True

    def __init__(self, firecrawl_provider: Optional[FirecrawlProvider] = None):
        super().__init__()
        self.firecrawl = firecrawl_provider or FirecrawlProvider()

    def run(self, url: str = "", search: Optional[str] = None, **kwargs) -> Any:
        """Map target domain and return discovered URL list."""
        if not url:
            raise ValueError("URL parameter is required for map_site.")

        links = self.firecrawl.map(url=url, search=search)
        return {
            "root_url": url,
            "search_filter": search,
            "total_links_discovered": len(links),
            "links": links,
            "provider": "firecrawl",
        }
