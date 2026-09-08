"""
Autonomous Web Crawler.
Traverses seed documents, extracts child hyperlinks, enforces depth/budget bounds, and resolves citations.
"""

from typing import List, Dict, Set, Optional, Generator
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from src.internet.fetcher.fetcher import WebFetcher
from src.internet.crawler.robots import RobotsPolicyManager
from src.internet.crawler.rate_limiter import DomainRateLimiter
from src.internet.providers.base import FetchResult
from src.core.logging import logger


class CrawledPage(BaseModel):
    url: str
    final_url: str
    parent_url: Optional[str] = None
    depth: int = 0
    fetch_result: FetchResult
    discovered_links: List[str] = Field(default_factory=list)
    title: Optional[str] = None


class AutonomousWebCrawler:
    """Traverses the web frontier following citations and high-relevance links."""

    def __init__(
        self,
        fetcher: Optional[WebFetcher] = None,
        max_depth: int = 2,
        max_pages: int = 15,
        respect_robots: bool = True,
    ):
        self.fetcher = fetcher or WebFetcher()
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.robots = RobotsPolicyManager() if respect_robots else None
        self.rate_limiter = DomainRateLimiter(default_interval_seconds=0.3)
        self.visited_urls: Set[str] = set()
        self.visited_hashes: Set[str] = set()

    def crawl(self, seed_urls: List[str]) -> List[CrawledPage]:
        """Crawl starting from seed URLs up to max_depth and max_pages budget."""
        results: List[CrawledPage] = []
        queue: List[tuple] = [(u, None, 0) for u in seed_urls]  # (url, parent, depth)

        while queue and len(results) < self.max_pages:
            url, parent, depth = queue.pop(0)
            clean_url, _ = urldefrag(url)
            norm_url = clean_url.rstrip("/").lower()

            if norm_url in self.visited_urls or depth > self.max_depth:
                continue

            self.visited_urls.add(norm_url)

            # Check robots.txt
            if self.robots and not self.robots.is_allowed(clean_url):
                logger.info(f"Crawler: Skipping {clean_url} (disallowed by robots.txt)")
                continue

            # Apply domain rate limiter
            self.rate_limiter.wait_if_needed(clean_url)

            # Fetch
            res = self.fetcher.fetch(clean_url)
            if not res.is_success or res.content_hash in self.visited_hashes:
                continue

            self.visited_hashes.add(res.content_hash)

            # Extract outbound links if HTML
            discovered_links: List[str] = []
            title = None
            if "html" in res.content_type.lower() and res.raw_content:
                try:
                    soup = BeautifulSoup(res.raw_content, "html.parser")
                    title_tag = soup.find("title")
                    title = title_tag.get_text(strip=True) if title_tag else None

                    for a in soup.find_all("a", href=True):
                        href = a["href"].strip()
                        abs_url = urljoin(res.final_url, href)
                        parsed = urlparse(abs_url)
                        
                        # Filter valid HTTP links and exclude common media/tracking
                        if parsed.scheme in ["http", "https"] and not any(
                            abs_url.lower().endswith(ext)
                            for ext in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js", ".ico", ".mp4", ".zip"]
                        ):
                            discovered_links.append(abs_url)
                except Exception as e:
                    logger.warning(f"Error parsing links from {clean_url}: {e}")

            crawled_page = CrawledPage(
                url=clean_url,
                final_url=res.final_url,
                parent_url=parent,
                depth=depth,
                fetch_result=res,
                discovered_links=discovered_links[:25],
                title=title,
            )
            results.append(crawled_page)

            # Add discovered links to queue if under max depth
            if depth + 1 <= self.max_depth:
                for child_link in discovered_links[:5]:  # take top 5 child links per page
                    clean_child, _ = urldefrag(child_link)
                    if clean_child.rstrip("/").lower() not in self.visited_urls:
                        queue.append((clean_child, clean_url, depth + 1))

        logger.info(f"AutonomousWebCrawler completed crawl: {len(results)} pages acquired.")
        return results
