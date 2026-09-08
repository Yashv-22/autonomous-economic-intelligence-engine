"""
Web Crawl Tool implementation using AutonomousWebCrawler.
"""

from typing import Dict, Any, List, Optional
from src.tools.base import BaseTool
from src.models.schemas import ToolPermission
from src.internet.crawler.crawler import AutonomousWebCrawler


class CrawlTool(BaseTool):
    """Recursively traverses public links to discover linked research papers, articles, and citations."""

    name: str = "crawl_web_links"
    description: str = "Recursively discovers and acquires referenced research articles and datasets."
    permission_level: ToolPermission = ToolPermission.READ_ONLY
    requires_network: bool = True

    def __init__(self, crawler: Optional[AutonomousWebCrawler] = None):
        super().__init__()
        self.crawler = crawler or AutonomousWebCrawler()

    def run(self, seed_urls: List[str] = None, max_depth: int = 2, max_pages: int = 5, **kwargs) -> Any:
        """Crawl starting from seed URLs."""
        crawler = AutonomousWebCrawler(max_depth=max_depth, max_pages=max_pages)
        pages = crawler.crawl(seed_urls or [])

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
            }
            for p in pages
        ]
