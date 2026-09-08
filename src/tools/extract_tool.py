"""
HTML / Web Content Extraction Tool.
Parses raw HTML and structured text into clean, provenance-anchored SourceSpans.
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from src.tools.base import BaseTool
from src.models.schemas import ToolPermission, SourceSpan
from src.security.sanitizer import ContentSanitizer
from src.core.identifiers import compute_sha256


class ExtractTool(BaseTool):
    """Tool for extracting and segmenting text content into SourceSpans."""

    name: str = "extract_spans"
    description: str = "Extract clean text paragraphs and create cryptographic SourceSpans from raw HTML or text."
    permission_level: ToolPermission = ToolPermission.READ_ONLY
    requires_network: bool = False

    def run(
        self,
        raw_content: str = "",
        document_name: str = "",
        document_hash: str = "",
        source_url: Optional[str] = None,
        is_html: bool = False,
        **kwargs,
    ) -> List[SourceSpan]:
        """
        Extract clean, sanitized spans from raw content.
        """
        if is_html or "<html" in raw_content.lower() or "<body" in raw_content.lower() or "<p>" in raw_content.lower():
            soup = BeautifulSoup(raw_content, "html.parser")
            # Remove scripts, styles, navs
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()

            paragraphs = []
            for tag in soup.find_all(["p", "h1", "h2", "h3", "li", "blockquote", "article"]):
                text = tag.get_text(separator=" ", strip=True)
                if text and len(text) >= 25:
                    paragraphs.append(text)
        else:
            paragraphs = [p.strip() for p in raw_content.split("\n\n") if len(p.strip()) >= 25]

        spans: List[SourceSpan] = []
        for idx, para in enumerate(paragraphs):
            sanitized_para = ContentSanitizer.sanitize_untrusted_text(para)
            if len(sanitized_para) < 25:
                continue

            span_hash = compute_sha256(sanitized_para)
            spans.append(
                SourceSpan(
                    document_name=document_name,
                    document_hash=document_hash,
                    page_or_section=f"Section {idx + 1}",
                    paragraph_index=idx,
                    text=sanitized_para,
                    span_hash=span_hash,
                    source_url=source_url,
                )
            )

        return spans
