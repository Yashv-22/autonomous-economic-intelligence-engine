"""
Ingestion & Provenance Agent.
Discovers, fetches, and parses multi-format documents and web sources into cryptographic spans.
"""

from typing import List, Dict, Any, Optional
from src.agents.base import BaseAgent, AgentContext
from src.models.schemas import ToolPermission, SourceSpan, ProvenanceMetadata
from src.ingestion.document_parser import DocumentIngestionEngine
from src.provenance.ledger import ProvenanceLedger
from src.core.identifiers import compute_sha256


class IngestionAgent(BaseAgent):
    """Specialized agent for acquiring and cryptographically registering source documents."""

    name: str = "IngestionAgent"
    role: str = "Source Acquisition & Provenance Specialist"
    description: str = "Acquires documents from filesystem or web, parses spans, and anchors Merkle provenance."
    allowed_tools: List[str] = ["search_sources", "fetch_web_content", "extract_spans"]
    permission_level: ToolPermission = ToolPermission.READ_ONLY

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.doc_engine = DocumentIngestionEngine()
        self.provenance_ledger = ProvenanceLedger()

    def run(
        self,
        context: AgentContext,
        local_dir: Optional[str] = None,
        search_queries: Optional[List[str]] = None,
        **kwargs
    ) -> List[SourceSpan]:
        """
        Ingest local documents and/or search & fetch online documents.
        """
        all_spans: List[SourceSpan] = []

        # 1. Ingest local directory files if specified
        if local_dir:
            local_spans = self.doc_engine.ingest_directory(local_dir, supported_extensions=[".pdf", ".docx", ".txt", ".md"])
            all_spans.extend(local_spans)

        # 2. Acquire via search and fetch tools if queries provided
        if search_queries:
            import concurrent.futures
            from datetime import datetime, timezone

            discovered_items: List[Dict[str, Any]] = []
            seen_urls = set()
            for q in search_queries[:3]:
                search_res = self.invoke_tool(context, "search_sources", query=q, max_results=5)
                if search_res.success and search_res.output:
                    for item in search_res.output:
                        url = item.get("url")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            discovered_items.append(item)

            # Ingest rich search snippets directly as guaranteed provenance spans
            for item in discovered_items:
                snippet = item.get("snippet", "").strip()
                title = item.get("title") or "Web Discovery Source"
                url = item.get("url") or ""
                if snippet and len(snippet) >= 30:
                    s_hash = compute_sha256(snippet)
                    all_spans.append(
                        SourceSpan(
                            document_name=title,
                            document_hash=s_hash,
                            page_or_section="Abstract / Search Evidence",
                            paragraph_index=0,
                            text=snippet,
                            span_hash=s_hash,
                            source_url=url,
                            start_char=0,
                            end_char=len(snippet),
                        )
                    )

            # Concurrent web fetch for top URLs (with rapid timeout and raw_html support)
            urls_to_fetch = [it.get("url") for it in discovered_items[:3] if it.get("url")]
            if urls_to_fetch:
                def _fetch_and_extract_url(target_url: str) -> List[SourceSpan]:
                    try:
                        fetch_res = self.invoke_tool(context, "fetch_web_content", url=target_url, timeout_seconds=3.0)
                        if fetch_res.success and fetch_res.output:
                            data = fetch_res.output
                            raw_body = data.get("content") or data.get("raw_html") or data.get("text_preview") or ""
                            if raw_body:
                                extract_res = self.invoke_tool(
                                    context,
                                    "extract_spans",
                                    raw_content=raw_body,
                                    document_name=data.get("url", target_url),
                                    document_hash=data.get("document_hash") or compute_sha256(raw_body),
                                    source_url=target_url,
                                    is_html=data.get("content_type") == "text/html" or "<html" in str(raw_body).lower(),
                                )
                                if extract_res.success and extract_res.output:
                                    return extract_res.output
                    except Exception as err:
                        logger.warning(f"Error fetching/extracting '{target_url}': {err}")
                    return []

                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(urls_to_fetch), 4)) as executor:
                    for span_list in executor.map(_fetch_and_extract_url, urls_to_fetch):
                        if span_list:
                            all_spans.extend(span_list)

        # Register in Provenance Ledger
        self.provenance_ledger.register_spans(all_spans)
        return all_spans
