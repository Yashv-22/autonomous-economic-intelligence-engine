"""
Agent Reach Tool implementation.
Exposes multi-platform Internet capabilities (Web, GitHub, YouTube, RSS, V2EX, Bilibili)
as a callable system tool with permission gating and provenance tracking.
"""

from typing import Dict, Any, List, Optional
from src.tools.base import BaseTool
from src.models.schemas import ToolPermission
from src.internet.providers.agent_reach_provider import (
    AgentReachSearchProvider,
    AgentReachFetchProvider,
)
from src.core.logging import logger


class AgentReachTool(BaseTool):
    """
    Executes multi-platform Internet research queries and content retrieval
    using Agent Reach routing and backends.
    """

    name: str = "agent_reach"
    description: str = (
        "Multi-platform Internet research tool. Supports full-web search, "
        "GitHub repository/code search, YouTube transcript extraction, "
        "RSS/Atom feed reading, and Jina Reader clean markdown web fetching."
    )
    permission_level: ToolPermission = ToolPermission.READ_ONLY
    requires_network: bool = True

    def __init__(
        self,
        search_provider: Optional[AgentReachSearchProvider] = None,
        fetch_provider: Optional[AgentReachFetchProvider] = None,
    ):
        super().__init__()
        self.search_provider = search_provider or AgentReachSearchProvider()
        self.fetch_provider = fetch_provider or AgentReachFetchProvider()

    def run(
        self,
        action: str = "search",
        query: str = "",
        url: str = "",
        max_results: int = 5,
        channel: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Execute an Agent Reach action:
          - search: multi-platform search (web, github, v2ex, bilibili)
          - read_url: read arbitrary web page via Jina Reader markdown
          - read_rss: read and parse RSS/Atom feed
          - youtube_transcript: extract YouTube subtitles and metadata
          - doctor: check platform capabilities and backends
        """
        action_lower = action.lower().strip()

        if action_lower == "search":
            if not query:
                raise ValueError("Query parameter is required for 'search' action.")
            results = self.search_provider.search(
                query=query,
                max_results=max_results,
                channel=channel,
            )
            return [r.model_dump() for r in results]

        elif action_lower in ("fetch", "read_url", "read_page"):
            if not url:
                raise ValueError("URL parameter is required for 'read_url' action.")
            fetch_res = self.fetch_provider.fetch(url)
            if not fetch_res.is_success:
                raise RuntimeError(fetch_res.error_message or "Agent Reach fetch failed.")
            return {
                "url": fetch_res.url,
                "final_url": fetch_res.final_url,
                "status_code": fetch_res.status_code,
                "content_type": fetch_res.content_type,
                "content_hash": fetch_res.content_hash,
                "document_hash": fetch_res.content_hash,
                "size_bytes": fetch_res.size_bytes,
                "latency_ms": fetch_res.latency_ms,
                "text_content": fetch_res.raw_content.decode("utf-8", errors="replace"),
                "headers": fetch_res.headers,
                "provider": "agent_reach",
            }

        elif action_lower in ("read_rss", "rss"):
            if not url:
                raise ValueError("URL parameter is required for 'read_rss' action.")
            fetch_res = self.fetch_provider._fetch_rss(url, start_time=0.0)
            if not fetch_res.is_success:
                raise RuntimeError(fetch_res.error_message or "Agent Reach RSS fetch failed.")
            return {
                "url": fetch_res.url,
                "content_type": fetch_res.content_type,
                "content_hash": fetch_res.content_hash,
                "text_content": fetch_res.raw_content.decode("utf-8", errors="replace"),
                "provider": "agent_reach",
            }

        elif action_lower in ("youtube", "youtube_transcript"):
            if not url:
                raise ValueError("URL parameter is required for 'youtube_transcript' action.")
            fetch_res = self.fetch_provider._fetch_youtube(url, start_time=0.0)
            if not fetch_res.is_success:
                raise RuntimeError(fetch_res.error_message or "Agent Reach YouTube extraction failed.")
            return {
                "url": fetch_res.url,
                "content_type": fetch_res.content_type,
                "content_hash": fetch_res.content_hash,
                "text_content": fetch_res.raw_content.decode("utf-8", errors="replace"),
                "provider": "agent_reach",
            }

        elif action_lower == "doctor":
            from agent_reach.doctor import check_all
            from agent_reach.config import Config
            cfg = Config()
            report_dict = check_all(cfg)
            return {
                channel_name: {
                    "status": info.get("status"),
                    "backend": info.get("backend"),
                    "message": info.get("message"),
                }
                for channel_name, info in report_dict.items()
            }

        else:
            raise ValueError(
                f"Unknown Agent Reach action '{action}'. Supported actions: "
                "search, read_url, read_rss, youtube_transcript, doctor."
            )
