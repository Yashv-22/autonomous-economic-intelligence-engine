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
    allowed_tools: List[str] = [
        "search_sources",
        "fetch_web_content",
        "extract_spans",
        "agent_reach",
        "scrape_page",
        "deep_crawl",
        "map_site",
        "render_dynamic_page",
        "browser_navigate",
    ]
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
        Uses concurrent harvesting across Agent Reach, Exa, and Adaptive Router.
        """
        all_spans: List[SourceSpan] = []
        seen_span_hashes = set()

        def _add_span(sp: SourceSpan):
            if sp.span_hash not in seen_span_hashes:
                seen_span_hashes.add(sp.span_hash)
                all_spans.append(sp)

        # 1. Ingest local directory files only if an explicit external directory is provided
        if local_dir and local_dir not in [".", "./"] and os.path.exists(local_dir):
            local_spans = self.doc_engine.ingest_directory(local_dir, supported_extensions=[".pdf", ".docx", ".txt", ".md"])
            for sp in local_spans:
                _add_span(sp)

        # 2. Acquire via search and fetch tools if queries provided
        if search_queries:
            import concurrent.futures

            discovered_items: List[Dict[str, Any]] = []
            seen_urls = set()

            # Execute searches concurrently across queries for maximum speed
            def _execute_single_query(q: str) -> List[Dict[str, Any]]:
                search_res = self.invoke_tool(context, "search_sources", query=q, max_results=5)
                if search_res.success and search_res.output:
                    return search_res.output
                return []

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(search_queries), 6)) as s_exec:
                for items in s_exec.map(_execute_single_query, search_queries):
                    for item in items:
                        url = item.get("url")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            discovered_items.append(item)

            # Ingest rich search highlights & snippets directly as guaranteed provenance spans
            for item in discovered_items:
                title = item.get("title") or "Web Discovery Source"
                url = item.get("url") or ""
                metadata = item.get("metadata") or {}

                # A. Direct Exa verbatim highlights (Zero network fetch latency)
                highlights = metadata.get("highlights") or []
                if isinstance(highlights, list):
                    for h_idx, h in enumerate(highlights):
                        h_clean = h.strip()
                        if len(h_clean) >= 30:
                            h_hash = compute_sha256(h_clean)
                            _add_span(
                                SourceSpan(
                                    document_name=title,
                                    document_hash=h_hash,
                                    page_or_section=f"Verbatim Evidence / Highlight #{h_idx+1}",
                                    paragraph_index=h_idx,
                                    text=h_clean,
                                    span_hash=h_hash,
                                    source_url=url,
                                    start_char=0,
                                    end_char=len(h_clean),
                                )
                            )

                # B. Snippet fallback if highlights not available
                snippet = item.get("snippet", "").strip()
                if snippet and len(snippet) >= 30 and not highlights:
                    s_hash = compute_sha256(snippet)
                    _add_span(
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

            # Concurrent web fetch for top URLs via Adaptive Router
            urls_to_fetch = [it.get("url") for it in discovered_items[:8] if it.get("url")]
            if urls_to_fetch:
                def _fetch_and_extract_url(target_url: str) -> List[SourceSpan]:
                    try:
                        fetch_res = self.invoke_tool(context, "fetch_web_content", url=target_url, timeout_seconds=4.0)
                        if fetch_res.success and fetch_res.output:
                            data = fetch_res.output
                            raw_body = data.get("content") or data.get("raw_html") or data.get("text_preview") or ""
                            if raw_body and len(raw_body) > 100:
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

                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(urls_to_fetch), 8)) as executor:
                    for span_list in executor.map(_fetch_and_extract_url, urls_to_fetch):
                        if span_list:
                            for sp in span_list:
                                _add_span(sp)

        # Register in Provenance Ledger
        self.provenance_ledger.register_spans(all_spans)
        return all_spans
