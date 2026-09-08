"""
Wikipedia Search and Reference Provider.
Queries the official Wikipedia API for encyclopedic summaries, organizational profiles, and citations.
"""

import urllib.request
import urllib.parse
import json
from typing import List, Optional

from src.internet.providers.base import BaseSearchProvider, SearchResultItem
from src.core.logging import logger


class WikipediaSearchProvider(BaseSearchProvider):
    """Encyclopedic search via Wikipedia Opensearch / REST API."""

    def __init__(self, user_agent: Optional[str] = None):
        self.user_agent = user_agent or "AutonomousResearchEngine/1.0 (research-bot)"

    @property
    def provider_name(self) -> str:
        return "wikipedia"

    def search(self, query: str, max_results: int = 5, **kwargs) -> List[SearchResultItem]:
        """Execute search query against Wikipedia API with keyword extraction and rapid timeout."""
        import re
        stop_words = {"what", "when", "where", "which", "while", "rather", "than", "with", "from", "into", "that", "this", "these", "those", "have", "more", "most", "about", "other", "their", "there", "they", "person", "newly", "starting", "getting", "field", "suffering"}
        clean_words = [w for w in re.findall(r"\b[A-Za-z0-9_-]{3,}\b", query) if w.lower() not in stop_words]
        compact_query = " ".join(clean_words[:3]) if clean_words else (query[:30].strip())

        encoded_query = urllib.parse.quote_plus(compact_query)
        url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={encoded_query}&limit={max_results}&namespace=0&format=json"

        req = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
        )

        results: List[SearchResultItem] = []
        try:
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
                if len(data) >= 4:
                    titles = data[1]
                    snippets = data[2]
                    urls = data[3]

                    for rank, (title, snippet, page_url) in enumerate(zip(titles, snippets, urls), 1):
                        results.append(
                            SearchResultItem(
                                title=title,
                                url=page_url,
                                snippet=snippet,
                                source_domain="en.wikipedia.org",
                                provider=self.provider_name,
                                rank=rank,
                                source_type="encyclopedic",
                                relevance_score=max(0.3, 0.9 - (rank * 0.1)),
                            )
                        )

            logger.info(f"WikipediaSearchProvider found {len(results)} entries for query: '{query}'")
        except Exception as e:
            logger.warning(f"Wikipedia search failed for query '{query}': {e}")

        return results
