"""
Internet Normalization Module.
Parses raw HTML, Markdown, and JSON, strips navigational boilerplate,
and extracts verifiable text spans with source metadata.
"""

from typing import List, Dict, Any, Optional
from src.internet.providers.base import FetchResult
from src.internet.parsers.web_parser import WebContentParser
from src.core.identifiers import compute_sha256
from src.core.logging import logger


class NormalizedSourceDocument:
    """Represents a normalized external source document ready for claim extraction."""

    def __init__(
        self,
        url: str,
        title: str,
        clean_text: str,
        chunks: List[str],
        content_hash: str,
        metadata: Dict[str, Any],
    ):
        self.url = url
        self.title = title
        self.clean_text = clean_text
        self.chunks = chunks
        self.content_hash = content_hash
        self.metadata = metadata


class NormalizationEngine:
    """
    Normalizes heterogeneous web content into standardized, auditable text chunks.
    """

    def __init__(self, parser: Optional[WebContentParser] = None):
        self.parser = parser or WebContentParser()

    def normalize(
        self,
        fetched_sources: List[FetchResult],
        chunk_size: int = 500,
    ) -> List[NormalizedSourceDocument]:
        """
        Parse raw fetched HTML/markdown into normalized text documents and discrete spans.
        """
        documents: List[NormalizedSourceDocument] = []

        for item in fetched_sources:
            raw_text = (
                item.raw_content.decode("utf-8", errors="replace")
                if isinstance(item.raw_content, bytes)
                else str(item.raw_content)
            )
            try:
                parsed = self.parser.parse(raw_text, url=item.url)
                clean_text = parsed.text if hasattr(parsed, "text") else raw_text
                title = parsed.title if hasattr(parsed, "title") and parsed.title else item.url
            except Exception as e:
                logger.debug(f"Parser fallback to plain text for '{item.url}': {e}")
                clean_text = raw_text
                title = item.url

            # Segment into discrete sentences / chunks
            paragraphs = [p.strip() for p in clean_text.split("\n\n") if len(p.strip()) > 30]
            if not paragraphs:
                paragraphs = [clean_text[:chunk_size]] if clean_text.strip() else []

            doc_hash = compute_sha256(clean_text)
            doc = NormalizedSourceDocument(
                url=item.url,
                title=title,
                clean_text=clean_text,
                chunks=paragraphs,
                content_hash=doc_hash,
                metadata={
                    "status_code": item.status_code,
                    "content_type": item.content_type,
                    "fetched_at": getattr(item, "fetched_at", None),
                },
            )
            documents.append(doc)

        logger.info(f"NormalizationEngine: Normalized {len(documents)} documents ({sum(len(d.chunks) for d in documents)} text spans).")
        return documents
