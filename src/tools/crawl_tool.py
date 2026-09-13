"""
Web Crawl Tool implementation using AutonomousWebCrawler.
"""

from typing import Dict, Any, List, Optional
from src.tools.base import BaseTool
from src.models.schemas import ToolPermission
from src.internet.crawler.crawler import AutonomousWebCrawler
from src.internet.providers.firecrawl_provider import FirecrawlProvider


class CrawlTool(BaseTool):
    """Recursively traverses public links to discover linked research papers, articles, and citations."""

    name: str = "crawl_web_links"
    description: str = "Recursively discovers and acquires referenced research articles and datasets."
    permission_level: ToolPermission = ToolPermission.READ_ONLY
    requires_network: bool = True

    def __init__(
        self,
        crawler: Optional[AutonomousWebCrawler] = None,
        firecrawl: Optional[FirecrawlProvider] = None,
    ):
        super().__init__()
        self.crawler = crawler or AutonomousWebCrawler()
        self.firecrawl = firecrawl or FirecrawlProvider()

    def run(
        self,
        seed_urls: List[str] = None,
        max_depth: int = 2,
        max_pages: int = 5,
        use_firecrawl: bool = False,
        **kwargs,
    ) -> Any:
        """Crawl starting from seed URLs."""
        seeds = seed_urls or []

        # Try Firecrawl deep crawl if requested and available
        if use_firecrawl and seeds:
            fc_results = []
            for seed in seeds[:2]:
                fc_pages = self.firecrawl.crawl(seed_url=seed, max_depth=max_depth, max_pages=max_pages)
                if fc_pages:
                    fc_results.extend(fc_pages)
            if fc_results:
                return [
                    {
                        "url": res.url,
                        "final_url": res.final_url,
                        "parent_url": None,
                        "depth": 1,
                        "title": res.metadata.get("title") if res.metadata else res.url,
                        "content_hash": res.content_hash,
                        "size_bytes": res.size_bytes,
                        "discovered_links_count": len(res.links),
                        "provider": "firecrawl",
                    }
                    for res in fc_results[:max_pages]
                ]

        # Standard AutonomousWebCrawler
        crawler = AutonomousWebCrawler(max_depth=max_depth, max_pages=max_pages)
        pages = crawler.crawl(seeds)

        return [
            {
                "url": p.url,
                "final_url": p.final_url,
                "parent_url": p.parent_url,
                "depth": p.depth,
                "title": p.title,
                "content_hash": p.fetch_result.content_hash,
                "size_bytes": p.fetch_result.size_bytes,
                "discovered_links_count": len(p.discovered_links),
                "provider": "native_crawler",
            }
            for p in pages
        ]
