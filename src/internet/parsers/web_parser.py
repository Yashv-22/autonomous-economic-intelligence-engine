"""
Web Document Parsers.
Extracts clean, sanitized text paragraphs and citations from raw HTML, PDFs, and plain text.
"""

import io
from typing import List, Optional
from bs4 import BeautifulSoup
from pypdf import PdfReader

from src.models.schemas import SourceSpan
from src.core.identifiers import compute_sha256
from src.security.sanitizer import ContentSanitizer
from src.core.logging import logger


class WebContentParser:
    """Parses raw HTML/PDF response bytes into cryptographically hashed SourceSpan items."""

    @staticmethod
    def parse_html(raw_bytes: bytes, source_url: str, doc_name: str) -> List[SourceSpan]:
        """Extract clean paragraphs from HTML bytes."""
        try:
            html_text = raw_bytes.decode("utf-8", errors="replace")
            soup = BeautifulSoup(html_text, "html.parser")

            # Remove scripts, styles, navigations, footers
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside", "svg"]):
                tag.decompose()

            spans: List[SourceSpan] = []
            doc_hash = compute_sha256(raw_bytes)

            # Look for main content container or fallback to all paragraphs
            main_container = soup.find("main") or soup.find("article") or soup.body or soup
            paragraphs = main_container.find_all(["p", "h1", "h2", "h3", "li", "blockquote"])

            idx = 0
            for p in paragraphs:
                text = p.get_text(strip=True)
                # Filter noise
                if len(text) < 40:
                    continue

                # Defuse any prompt injection markers
                clean_text = ContentSanitizer.sanitize_untrusted_text(text)
                span_hash = compute_sha256(clean_text)

                spans.append(
                    SourceSpan(
                        document_name=doc_name,
                        document_hash=doc_hash,
                        page_or_section=f"Section {idx+1}",
                        paragraph_index=idx,
                        text=clean_text,
                        span_hash=span_hash,
                        source_url=source_url,
                    )
                )
                idx += 1

            return spans
        except Exception as e:
            logger.warning(f"Error parsing HTML from {source_url}: {e}")
            return []

    @staticmethod
    def parse_pdf(raw_bytes: bytes, source_url: str, doc_name: str) -> List[SourceSpan]:
        """Extract clean text spans from raw PDF bytes."""
        try:
            reader = PdfReader(io.BytesIO(raw_bytes))
            doc_hash = compute_sha256(raw_bytes)
            spans: List[SourceSpan] = []
            idx = 0

            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                paragraphs = [p.strip() for p in page_text.split("\n\n") if len(p.strip()) >= 40]

                for p in paragraphs:
                    clean_text = ContentSanitizer.sanitize_untrusted_text(p.replace("\n", " "))
                    span_hash = compute_sha256(clean_text)

                    spans.append(
                        SourceSpan(
                            document_name=doc_name,
                            document_hash=doc_hash,
                            page_or_section=f"Page {page_num}",
                            paragraph_index=idx,
                            text=clean_text,
                            span_hash=span_hash,
                            source_url=source_url,
                        )
                    )
                    idx += 1

            return spans
        except Exception as e:
            logger.warning(f"Error parsing PDF from {source_url}: {e}")
            return []

    @staticmethod
    def parse_markdown(raw_bytes: bytes, source_url: str, doc_name: str) -> List[SourceSpan]:
        """Extract clean text spans from raw Markdown or plaintext bytes."""
        try:
            md_text = raw_bytes.decode("utf-8", errors="replace")
            doc_hash = compute_sha256(raw_bytes)
            spans: List[SourceSpan] = []
            idx = 0

            # Split on double newlines for logical paragraphs/sections
            blocks = [b.strip() for b in md_text.split("\n\n") if len(b.strip()) >= 30]
            for b in blocks:
                clean_text = ContentSanitizer.sanitize_untrusted_text(b.replace("\n", " "))
                span_hash = compute_sha256(clean_text)

                spans.append(
                    SourceSpan(
                        document_name=doc_name,
                        document_hash=doc_hash,
                        page_or_section=f"Section {idx+1}",
                        paragraph_index=idx,
                        text=clean_text,
                        span_hash=span_hash,
                        source_url=source_url,
                    )
                )
                idx += 1

            return spans
        except Exception as e:
            logger.warning(f"Error parsing Markdown from {source_url}: {e}")
            return []
