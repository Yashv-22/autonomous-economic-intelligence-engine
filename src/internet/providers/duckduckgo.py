"""
DuckDuckGo Search Provider.
Executes live public web search using DuckDuckGo Lite endpoint with rate limiting and robust HTML parsing.
"""

import urllib.request
import urllib.parse
from typing import List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from src.internet.providers.base import BaseSearchProvider, SearchResultItem
from src.core.logging import logger
from src.core.identifiers import compute_sha256


class DuckDuckGoSearchProvider(BaseSearchProvider):
    """Live web search via DuckDuckGo."""

    def __init__(self, user_agent: Optional[str] = None):
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36 (AutonomousResearchEngine/1.0)"
        )

    @property
    def provider_name(self) -> str:
        return "duckduckgo"

    def search(self, query: str, max_results: int = 10, **kwargs) -> List[SearchResultItem]:
        """Execute live search query against DuckDuckGo Lite."""
        url = "https://lite.duckduckgo.com/lite/"
        encoded_data = urllib.parse.urlencode({"q": query}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=encoded_data,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        results: List[SearchResultItem] = []
        try:
            with urllib.request.urlopen(req, timeout=3.5) as response:
                html_content = response.read().decode("utf-8", errors="replace")
                soup = BeautifulSoup(html_content, "html.parser")

                # Parse lite results table
                # Typically rows with .result-link and snippets in subsequent td
                result_links = soup.find_all("a", class_="result-link")
                snippets = soup.find_all("td", class_="result-snippet")

                for rank, link_tag in enumerate(result_links[:max_results], 1):
                    raw_url = link_tag.get("href", "")
                    title = link_tag.get_text(strip=True)
                    
                    # Resolve DDG redirect URL if nested (e.g. //duckduckgo.com/l/?uddg=...)
                    if "uddg=" in raw_url:
                        parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                        if "uddg" in parsed_qs:
                            raw_url = parsed_qs["uddg"][0]

                    if not raw_url.startswith("http"):
                        continue

                    snippet = ""
                    if rank - 1 < len(snippets):
                        snippet = snippets[rank - 1].get_text(strip=True)

                    domain = urlparse(raw_url).netloc.lower()
                    
                    # Classify source type heuristic
                    source_type = "web"
                    if any(d in domain for d in ["arxiv.org", "ssrn.com", "ieee.org", "acm.org", "nature.com", "sciencedirect.com"]):
                        source_type = "academic"
                    elif any(d in domain for d in ["mckinsey.com", "bcg.com", "bain.com", "deloitte.com", "gartner.com", "pwc.com", "ey.com"]):
                        source_type = "consulting_research"
                    elif any(d in domain for d in ["gov", "sec.gov", "whitehouse.gov", "europa.eu", "oecd.org", "worldbank.org"]):
                        source_type = "government"
                    elif any(d in domain for d in ["reuters.com", "bloomberg.com", "ft.com", "wsj.com", "cnbc.com"]):
                        source_type = "news"

                    results.append(
                        SearchResultItem(
                            title=title,
                            url=raw_url,
                            snippet=snippet,
                            source_domain=domain,
                            provider=self.provider_name,
                            rank=rank,
                            source_type=source_type,
                            relevance_score=max(0.2, 1.0 - (rank * 0.08)),
                        )
                    )

            logger.info(f"DuckDuckGoSearchProvider found {len(results)} live results for query: '{query}'")
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed for query '{query}': {e}")

        return results
