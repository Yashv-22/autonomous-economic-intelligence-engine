"""
Multi-Format Document Ingestion Engine with Cryptographic Span Provenance.
Supports PDF, DOCX, Markdown, Text, and HTML files with sentence boundary healing and sanitization.
"""

import hashlib
import os
import re
from abc import ABC, abstractmethod
from typing import List, Optional
import pypdf
import docx
from bs4 import BeautifulSoup

from src.models.schemas import SourceSpan, ProvenanceMetadata
from src.security.sanitizer import ContentSanitizer
from src.core.identifiers import compute_sha256
from src.core.errors import IngestionError


def clean_and_join_lines(text: str) -> str:
    """Heal broken line wraps and hyphenated words across line boundaries."""
    # 1. Join hyphenated line breaks (e.g. "organisa-\ntion" -> "organisation")
    text = re.sub(r"(\w+)-\n\s*(\w+)", r"\1\2", text)
    # 2. Join soft line breaks within sentences
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    cleaned_text = " ".join(lines)
    # 3. Normalize multiple spaces
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
    return cleaned_text


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> List[SourceSpan]:
        """Parse document and return a list of cryptographically hashed SourceSpans."""
        pass


class PDFParser(BaseParser):
    """High-fidelity PDF document parser with line healing and reference filtering."""

    def parse(self, file_path: str) -> List[SourceSpan]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            doc_hash = compute_sha256(file_bytes)
            doc_name = os.path.basename(file_path)

            reader = pypdf.PdfReader(file_path)
            spans: List[SourceSpan] = []
            global_para_idx = 0

            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if not page_text:
                    continue

                # Check if this page is strictly a bibliography/reference section
                is_reference_page = "reference library" in page_text.lower() or "tier 1 — primary empirical" in page_text.lower()

                # Segment by logical paragraph blocks
                paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
                if len(paragraphs) <= 1:
                    # Group lines into coherent multi-line blocks
                    raw_lines = [l.strip() for l in page_text.split("\n") if l.strip()]
                    current_block = []
                    for line in raw_lines:
                        current_block.append(line)
                        if line.endswith(".") or line.endswith(":") or len(current_block) >= 5:
                            paragraphs.append(" ".join(current_block))
                            current_block = []
                    if current_block:
                        paragraphs.append(" ".join(current_block))

                for para in paragraphs:
                    cleaned_para = clean_and_join_lines(para)
                    sanitized_para = ContentSanitizer.sanitize_untrusted_text(cleaned_para)
                    if len(sanitized_para) < 25:  # Skip trivial headers/footers
                        continue
                    # Tag reference section
                    section_tag = f"Page {page_idx + 1} (References)" if is_reference_page else f"Page {page_idx + 1}"

                    span_hash = compute_sha256(sanitized_para)
                    spans.append(
                        SourceSpan(
                            document_name=doc_name,
                            document_hash=doc_hash,
                            page_or_section=section_tag,
                            paragraph_index=global_para_idx,
                            text=sanitized_para,
                            span_hash=span_hash,
                        )
                    )
                    global_para_idx += 1

            return spans
        except Exception as e:
            raise IngestionError(f"Failed to parse PDF '{file_path}': {e}")


class DocxParser(BaseParser):
    """Microsoft Word DOCX document parser using python-docx."""

    def parse(self, file_path: str) -> List[SourceSpan]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DOCX file not found: {file_path}")

        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            doc_hash = compute_sha256(file_bytes)
            doc_name = os.path.basename(file_path)

            doc = docx.Document(file_path)
            spans: List[SourceSpan] = []
            global_para_idx = 0
            current_section = "Introduction"

            for p in doc.paragraphs:
                text = clean_and_join_lines(p.text)
                if not text:
                    continue

                if p.style.name.startswith("Heading"):
                    current_section = text

                sanitized_text = ContentSanitizer.sanitize_untrusted_text(text)
                if len(sanitized_text) >= 20:
                    span_hash = compute_sha256(sanitized_text)
                    spans.append(
                        SourceSpan(
                            document_name=doc_name,
                            document_hash=doc_hash,
                            page_or_section=current_section,
                            paragraph_index=global_para_idx,
                            text=sanitized_text,
                            span_hash=span_hash,
                        )
                    )
                    global_para_idx += 1

            # Ingest tables
            for t_idx, table in enumerate(doc.tables):
                for r_idx, row in enumerate(table.rows):
                    row_text = " | ".join([clean_and_join_lines(cell.text) for cell in row.cells if cell.text.strip()])
                    sanitized_row = ContentSanitizer.sanitize_untrusted_text(row_text)
                    if len(sanitized_row) >= 15:
                        span_hash = compute_sha256(sanitized_row)
                        spans.append(
                            SourceSpan(
                                document_name=doc_name,
                                document_hash=doc_hash,
                                page_or_section=f"Table {t_idx + 1} (Row {r_idx + 1})",
                                paragraph_index=global_para_idx,
                                text=sanitized_row,
                                span_hash=span_hash,
                            )
                        )
                        global_para_idx += 1

            return spans
        except Exception as e:
            raise IngestionError(f"Failed to parse DOCX '{file_path}': {e}")


class TextParser(BaseParser):
    """Markdown and Plaintext file parser."""

    def parse(self, file_path: str) -> List[SourceSpan]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                full_text = f.read()

            doc_hash = compute_sha256(full_text)
            doc_name = os.path.basename(file_path)
            spans: List[SourceSpan] = []
            global_para_idx = 0
            current_section = "General"

            for block in full_text.split("\n\n"):
                text = clean_and_join_lines(block)
                if not text:
                    continue
                if text.startswith("#"):
                    current_section = text.split("\n")[0].strip("# ")

                sanitized_text = ContentSanitizer.sanitize_untrusted_text(text)
                if len(sanitized_text) >= 20:
                    span_hash = compute_sha256(sanitized_text)
                    spans.append(
                        SourceSpan(
                            document_name=doc_name,
                            document_hash=doc_hash,
                            page_or_section=current_section,
                            paragraph_index=global_para_idx,
                            text=sanitized_text,
                            span_hash=span_hash,
                        )
                    )
                    global_para_idx += 1

            return spans
        except Exception as e:
            raise IngestionError(f"Failed to parse Text/MD '{file_path}': {e}")


class HTMLParser(BaseParser):
    """HTML and Web page document parser."""

    def parse(self, file_path: str) -> List[SourceSpan]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"HTML file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                html_content = f.read()

            doc_hash = compute_sha256(html_content)
            doc_name = os.path.basename(file_path)

            soup = BeautifulSoup(html_content, "html.parser")
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()

            spans: List[SourceSpan] = []
            global_para_idx = 0

            for tag in soup.find_all(["p", "h1", "h2", "h3", "li", "blockquote", "article"]):
                text = tag.get_text(separator=" ", strip=True)
                cleaned = clean_and_join_lines(text)
                sanitized = ContentSanitizer.sanitize_untrusted_text(cleaned)
                if len(sanitized) >= 25:
                    span_hash = compute_sha256(sanitized)
                    spans.append(
                        SourceSpan(
                            document_name=doc_name,
                            document_hash=doc_hash,
                            page_or_section="Web Article",
                            paragraph_index=global_para_idx,
                            text=sanitized,
                            span_hash=span_hash,
                        )
                    )
                    global_para_idx += 1

            return spans
        except Exception as e:
            raise IngestionError(f"Failed to parse HTML '{file_path}': {e}")


class DocumentIngestionEngine:
    """Unified document ingestion coordinator supporting heterogeneous file formats."""

    def __init__(self):
        self.parsers = {
            ".pdf": PDFParser(),
            ".docx": DocxParser(),
            ".txt": TextParser(),
            ".md": TextParser(),
            ".html": HTMLParser(),
            ".htm": HTMLParser(),
        }

    def ingest_file(self, file_path: str) -> List[SourceSpan]:
        ext = os.path.splitext(file_path)[1].lower()
        parser = self.parsers.get(ext)
        if not parser:
            raise IngestionError(f"Unsupported file format: {ext} for file {file_path}")
        return parser.parse(file_path)

    def ingest_directory(self, dir_path: str, supported_extensions: List[str] = None) -> List[SourceSpan]:
        if supported_extensions is None:
            supported_extensions = [".pdf", ".docx", ".txt", ".md", ".html"]

        ignored_dirs = {
            ".git",
            "node_modules",
            ".venv",
            "venv",
            "__pycache__",
            "dist",
            "build",
            "scratch",
            ".gemini",
            "infrastructure",
            "vendor",
            "backups",
            "output",
            "output_audit_test",
        }
        all_spans: List[SourceSpan] = []
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith(".")]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_extensions and not file.startswith("~$"):
                    full_path = os.path.join(root, file)
                    spans = self.ingest_file(full_path)
                    all_spans.extend(spans)
        return all_spans
