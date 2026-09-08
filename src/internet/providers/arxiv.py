"""
ArXiv Academic Search Provider.
Queries the official arXiv Export API for peer-reviewed preprints and research papers.
"""

import urllib.request
import urllib.parse
from typing import List, Optional
import xml.etree.ElementTree as ET

from src.internet.providers.base import BaseSearchProvider, SearchResultItem
from src.core.logging import logger


class ArXivSearchProvider(BaseSearchProvider):
    """Live academic paper search via export.arxiv.org API."""

    def __init__(self, user_agent: Optional[str] = None):
        self.user_agent = user_agent or "AutonomousResearchEngine/1.0 (academic-researcher)"

    @property
    def provider_name(self) -> str:
        return "arxiv"

    def search(self, query: str, max_results: int = 10, **kwargs) -> List[SearchResultItem]:
        """Execute academic search query against arXiv API with concise keyword extraction and fail-fast timeout."""
        import re
        stop_words = {"what", "when", "where", "which", "while", "rather", "than", "with", "from", "into", "that", "this", "these", "those", "have", "more", "most", "about", "other", "their", "there", "they", "person", "newly", "starting", "getting", "field", "suffering", "traditional", "online"}
        clean_words = [w for w in re.findall(r"\b[A-Za-z0-9_-]{3,}\b", query) if w.lower() not in stop_words]
        compact_query = " ".join(clean_words[:4]) if clean_words else (query[:40].strip())

        encoded_query = urllib.parse.quote_plus(compact_query)
        url = f"https://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"

        req = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent, "Accept": "application/atom+xml"},
        )

        results: List[SearchResultItem] = []
        try:
            with urllib.request.urlopen(req, timeout=3.5) as response:
                xml_data = response.read().decode("utf-8", errors="replace")
                root = ET.fromstring(xml_data)

                # Atom XML namespace
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", ns)

                for rank, entry in enumerate(entries[:max_results], 1):
                    title_elem = entry.find("atom:title", ns)
                    summary_elem = entry.find("atom:summary", ns)
                    published_elem = entry.find("atom:published", ns)
                    id_elem = entry.find("atom:id", ns)

                    title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else "Untitled Paper"
                    snippet = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None and summary_elem.text else ""
                    published = published_elem.text.strip() if published_elem is not None and published_elem.text else None
                    paper_url = id_elem.text.strip() if id_elem is not None and id_elem.text else ""

                    # Find PDF link if available
                    pdf_url = paper_url
                    for link in entry.findall("atom:link", ns):
                        if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                            pdf_url = link.get("href", paper_url)

                    results.append(
                        SearchResultItem(
                            title=title,
                            url=paper_url or pdf_url,
                            snippet=snippet[:400],
                            source_domain="arxiv.org",
                            provider=self.provider_name,
                            rank=rank,
                            published_date=published,
                            source_type="academic",
                            relevance_score=max(0.3, 1.0 - (rank * 0.06)),
                            metadata={"arxiv_id": paper_url, "pdf_url": pdf_url},
                        )
                    )

            logger.info(f"ArXivSearchProvider found {len(results)} academic papers for query: '{query}'")
        except Exception as e:
            logger.warning(f"ArXiv search failed for query '{query}': {e}")

        return results
