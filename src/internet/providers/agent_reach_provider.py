"""
Agent Reach Internet Provider Adapter.
Integrates Agent Reach as a modular, provider-agnostic search and fetch capability.
Enforces SSRF prevention, prompt injection sanitization, and cryptographic provenance tagging.
"""

import os
import json
import time
import shutil
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from src.internet.providers.base import (
    BaseSearchProvider,
    BaseFetchProvider,
    SearchResultItem,
    FetchResult,
)
from src.security.network import network_validator
from src.security.sanitizer import ContentSanitizer
from src.core.identifiers import compute_sha256
from src.core.errors import SecurityViolationError
from src.core.logging import logger

# Import Agent Reach channels safely
try:
    from agent_reach.channels.web import WebChannel
    from agent_reach.channels.rss import RSSChannel
    from agent_reach.channels.youtube import YouTubeChannel
    from agent_reach.doctor import check_all
    AGENT_REACH_INSTALLED = True
except ImportError:
    AGENT_REACH_INSTALLED = False
    WebChannel = None
    RSSChannel = None
    YouTubeChannel = None
    check_all = None


class AgentReachSearchProvider(BaseSearchProvider):
    """
    Search provider backed by Agent Reach multi-channel discovery.
    Supports Exa AI semantic search (via mcporter), GitHub code/repos,
    Bilibili search, and V2EX hot topics, with automatic fallback.
    """

    def __init__(
        self,
        prefer_exa: bool = True,
        enable_github: bool = True,
        enable_v2ex: bool = True,
        enable_bilibili: bool = True,
    ):
        self.prefer_exa = prefer_exa
        self.enable_github = enable_github
        self.enable_v2ex = enable_v2ex
        self.enable_bilibili = enable_bilibili
        self._has_mcporter = bool(shutil.which("mcporter"))
        self._has_gh = bool(shutil.which("gh"))

    @property
    def provider_name(self) -> str:
        return "agent_reach"

    def search(
        self,
        query: str,
        max_results: int = 10,
        channel: Optional[str] = None,
        **kwargs,
    ) -> List[SearchResultItem]:
        """
        Execute search across supported Agent Reach channels.
        Routes to specific platform if channel is provided, or queries web/code.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        results: List[SearchResultItem] = []

        # 1. Platform-specific routing
        if channel == "github" or "github" in clean_query.lower():
            github_res = self._search_github(clean_query, max_results=max_results)
            if github_res:
                return github_res

        if channel == "v2ex":
            v2ex_res = self._search_v2ex(clean_query, max_results=max_results)
            if v2ex_res:
                return v2ex_res

        if channel == "bilibili":
            bili_res = self._search_bilibili(clean_query, max_results=max_results)
            if bili_res:
                return bili_res

        # 2. Exa Semantic Web Search via native REST API or mcporter
        exa_key = os.environ.get("EXA_API_KEY")
        if self.prefer_exa and (exa_key or self._has_mcporter):
            try:
                exa_results = self._search_exa(clean_query, max_results=max_results)
                if exa_results:
                    return exa_results
            except Exception as e:
                logger.warning(f"AgentReach Exa search error: {e}. Falling back.")

        # 3. Fallback: Search GitHub if query suggests code/library
        if any(term in clean_query.lower() for term in ["repo", "code", "github", "package", "library"]):
            github_res = self._search_github(clean_query, max_results=max_results)
            if github_res:
                return github_res

        # 4. Standard Web Fallback via DuckDuckGo provider to ensure uninterrupted search
        from src.internet.providers.duckduckgo import DuckDuckGoSearchProvider
        ddg = DuckDuckGoSearchProvider()
        ddg_results = ddg.search(clean_query, max_results=max_results)
        for r in ddg_results:
            r.provider = self.provider_name
            r.metadata["backend"] = "agent_reach_web_fallback"
            r.metadata["channel"] = "web"
        return ddg_results

    def _search_exa(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        """Execute semantic search via direct Exa REST API or mcporter Exa MCP integration."""
        api_key = os.environ.get("EXA_API_KEY")
        if api_key:
            try:
                url = "https://api.exa.ai/search"
                req_data = json.dumps({"query": query, "numResults": max_results, "useAutoprompt": True}).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=req_data,
                    headers={
                        "x-api-key": api_key,
                        "Content-Type": "application/json",
                        "User-Agent": "AutonomousResearchEngine/2.0",
                    },
                )
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    results_data = data.get("results", [])
                    items: List[SearchResultItem] = []
                    for idx, r in enumerate(results_data, 1):
                        r_url = r.get("url", "")
                        if not r_url:
                            continue
                        title = r.get("title", f"Exa Result #{idx}")
                        snippet = r.get("text", r.get("snippet", title))
                        parsed = urllib.parse.urlparse(r_url)
                        items.append(
                            SearchResultItem(
                                title=title,
                                url=r_url,
                                snippet=snippet[:300] if snippet else "",
                                source_domain=parsed.netloc or "exa.ai",
                                provider=self.provider_name,
                                rank=idx,
                                source_type="web",
                                relevance_score=max(0.2, 0.95 - (idx * 0.05)),
                                metadata={"backend": "exa_rest_api", "channel": "search"},
                            )
                        )
                    if items:
                        logger.info(f"AgentReach Exa REST API found {len(items)} live results for query: '{query}'")
                        return items
            except Exception as exa_rest_err:
                logger.warning(f"Direct Exa REST API failed ({exa_rest_err}). Falling back to mcporter.")

        if not self._has_mcporter:
            return []

        import subprocess
        cmd = [
            "mcporter", "call", "exa.web_search_exa",
            f"query={query}",
            f"numResults={max_results}",
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            shell=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"mcporter failed: {proc.stderr}")

        output = proc.stdout.strip()
        if not output:
            return []

        # Parse JSON output from mcporter
        items: List[SearchResultItem] = []
        try:
            data = json.loads(output)
            results_data = data if isinstance(data, list) else data.get("results", [])
            for idx, r in enumerate(results_data, 1):
                url = r.get("url", "")
                title = r.get("title", f"Exa Result #{idx}")
                snippet = r.get("text", r.get("snippet", ""))
                parsed = urllib.parse.urlparse(url)
                items.append(
                    SearchResultItem(
                        title=title,
                        url=url,
                        snippet=snippet[:300] if snippet else "",
                        source_domain=parsed.netloc or "exa.ai",
                        provider=self.provider_name,
                        rank=idx,
                        source_type="web",
                        relevance_score=0.9 - (idx * 0.05),
                        metadata={"backend": "exa_mcp", "channel": "search"},
                    )
                )
        except Exception as json_err:
            logger.debug(f"Could not parse Exa mcporter output as JSON: {json_err}")

        return items

    def _search_github(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        """Search GitHub public repositories via GitHub REST API or gh CLI."""
        import subprocess

        # Try gh CLI first if present
        if self._has_gh:
            try:
                cmd = [
                    "gh", "search", "repos", query,
                    "--limit", str(max_results),
                    "--json", "name,owner,description,url,stargazersCount",
                ]
                proc = subprocess.run(
                    cmd, capture_output=True, encoding="utf-8", errors="replace", timeout=12, shell=True
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    data = json.loads(proc.stdout)
                    results: List[SearchResultItem] = []
                    for idx, r in enumerate(data, 1):
                        results.append(
                            SearchResultItem(
                                title=f"{r.get('owner', {}).get('login', '')}/{r.get('name', '')}",
                                url=r.get("url", ""),
                                snippet=r.get("description", "") or "No description",
                                source_domain="github.com",
                                provider=self.provider_name,
                                rank=idx,
                                source_type="code_repository",
                                relevance_score=0.85,
                                metadata={
                                    "backend": "gh_cli",
                                    "channel": "github",
                                    "stars": r.get("stargazersCount", 0),
                                },
                            )
                        )
                    return results
            except Exception as e:
                logger.debug(f"gh CLI search failed, using GitHub REST API: {e}")

        # REST API fallback
        try:
            headers = {"User-Agent": "Researh-LLM-AgentReach/1.0", "Accept": "application/vnd.github.v3+json"}
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                headers["Authorization"] = f"token {token}"

            api_url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&per_page={max_results}"
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("items", [])
                results = []
                for idx, r in enumerate(items[:max_results], 1):
                    results.append(
                        SearchResultItem(
                            title=r.get("full_name", ""),
                            url=r.get("html_url", ""),
                            snippet=r.get("description", "") or "No description",
                            source_domain="github.com",
                            provider=self.provider_name,
                            rank=idx,
                            source_type="code_repository",
                            relevance_score=0.85,
                            metadata={
                                "backend": "github_rest_api",
                                "channel": "github",
                                "stars": r.get("stargazers_count", 0),
                            },
                        )
                    )
                return results
        except Exception as e:
            logger.warning(f"GitHub search API failed: {e}")
            return []

    def _search_v2ex(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        """Fetch V2EX hot topics matching query terms."""
        try:
            req = urllib.request.Request(
                "https://www.v2ex.com/api/topics/hot.json",
                headers={"User-Agent": "agent-reach/1.0", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                topics = json.loads(resp.read().decode("utf-8"))
                results: List[SearchResultItem] = []
                q_lower = query.lower()
                matched = [
                    t for t in topics
                    if q_lower in t.get("title", "").lower() or q_lower in t.get("content", "").lower()
                ] or topics[:max_results]

                for idx, t in enumerate(matched[:max_results], 1):
                    url = t.get("url", f"https://www.v2ex.com/t/{t.get('id', '')}")
                    results.append(
                        SearchResultItem(
                            title=t.get("title", ""),
                            url=url,
                            snippet=t.get("content", "")[:250] if t.get("content") else t.get("title", ""),
                            source_domain="v2ex.com",
                            provider=self.provider_name,
                            rank=idx,
                            source_type="tech_community",
                            relevance_score=0.80,
                            metadata={"backend": "v2ex_api", "channel": "v2ex", "replies": t.get("replies", 0)},
                        )
                    )
                return results
        except Exception as e:
            logger.warning(f"V2EX search failed: {e}")
            return []

    def _search_bilibili(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        """Search Bilibili public video search API."""
        try:
            encoded_q = urllib.parse.quote(query)
            api_url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={encoded_q}"
            req = urllib.request.Request(
                api_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.bilibili.com",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results: List[SearchResultItem] = []
                for item_group in data.get("data", {}).get("result", []):
                    if item_group.get("result_type") == "video":
                        for idx, v in enumerate(item_group.get("data", [])[:max_results], 1):
                            raw_title = v.get("title", "")
                            clean_title = raw_title.replace("<em class=\"keyword\">", "").replace("</em>", "")
                            arcurl = v.get("arcurl", "")
                            results.append(
                                SearchResultItem(
                                    title=clean_title,
                                    url=arcurl,
                                    snippet=v.get("description", "")[:250],
                                    source_domain="bilibili.com",
                                    provider=self.provider_name,
                                    rank=idx,
                                    source_type="video_community",
                                    relevance_score=0.75,
                                    metadata={"backend": "bilibili_search_api", "channel": "bilibili"},
                                )
                            )
                return results
        except Exception as e:
            logger.warning(f"Bilibili search failed: {e}")
            return []


class AgentReachFetchProvider(BaseFetchProvider):
    """
    Fetch provider backed by Agent Reach capabilities.
    Routes URLs to:
      - Jina Reader (for general web pages -> clean Markdown)
      - yt-dlp (for YouTube video metadata + subtitles/transcripts)
      - feedparser (for RSS/Atom feeds)
    Enforces strict SSRF protection and prompt-injection sanitization.
    """

    def __init__(self, user_agent: Optional[str] = None, max_bytes: int = 15_000_000):
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36 (AgentReach/1.5)"
        )
        self.max_bytes = max_bytes
        self.web_channel = WebChannel() if WebChannel else None
        self.rss_channel = RSSChannel() if RSSChannel else None
        self.yt_channel = YouTubeChannel() if YouTubeChannel else None

    def fetch(self, url: str, timeout_seconds: float = 4.0, max_bytes: Optional[int] = None) -> FetchResult:
        """Fetch content from target URL with security validation and channel routing."""
        limit_bytes = max_bytes or self.max_bytes
        start_time = time.time()

        # 1. Security & SSRF Validation
        try:
            canonical_url = network_validator.validate_url(url)
        except SecurityViolationError as sve:
            return FetchResult(
                url=url,
                final_url=url,
                status_code=403,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                is_success=False,
                error_message=f"SSRF or Network Security Violation: {sve}",
            )

        # 2. Channel Detection & Routing
        # A. YouTube Channel
        if self._is_youtube_url(canonical_url):
            return self._fetch_youtube(canonical_url, start_time)

        # B. RSS / Atom Channel
        if self._is_rss_url(canonical_url):
            return self._fetch_rss(canonical_url, start_time)

        # C. General Web via Jina Reader (with fallback)
        return self._fetch_web_jina(canonical_url, timeout_seconds, limit_bytes, start_time)

    def _is_youtube_url(self, url: str) -> bool:
        lower = url.lower()
        return "youtube.com/watch" in lower or "youtu.be/" in lower or "youtube.com/shorts" in lower

    def _is_rss_url(self, url: str) -> bool:
        lower = url.lower()
        return any(x in lower for x in ["/feed", "/rss", ".xml", "atom"])

    def _fetch_youtube(self, url: str, start_time: float) -> FetchResult:
        """Extract YouTube video metadata and subtitles using yt-dlp."""
        import subprocess

        cmd = [
            "yt-dlp",
            "--skip-download",
            "--dump-json",
            "--write-auto-sub",
            "--sub-lang", "en",
            url,
        ]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, encoding="utf-8", errors="replace", timeout=25, shell=True
            )
            latency = (time.time() - start_time) * 1000.0
            if proc.returncode == 0 and proc.stdout.strip():
                try:
                    data = json.loads(proc.stdout.strip().split("\n")[0])
                    title = data.get("title", "YouTube Video")
                    desc = data.get("description", "")
                    uploader = data.get("uploader", "")
                    tags = ", ".join(data.get("tags", [])[:10])

                    # Build clean markdown representation
                    md_text = (
                        f"# {title}\n\n"
                        f"- **Platform**: YouTube\n"
                        f"- **Uploader**: {uploader}\n"
                        f"- **URL**: {url}\n"
                        f"- **Tags**: {tags}\n\n"
                        f"## Description\n{desc}\n"
                    )

                    # Screen against prompt injections
                    is_suspicious, patterns = ContentSanitizer.detect_prompt_injection(md_text)
                    if is_suspicious:
                        md_text = ContentSanitizer.sanitize_untrusted_text(md_text)

                    raw_bytes = md_text.encode("utf-8")
                    content_hash = compute_sha256(raw_bytes)

                    return FetchResult(
                        url=url,
                        final_url=url,
                        status_code=200,
                        content_type="text/markdown; channel=youtube",
                        raw_content=raw_bytes,
                        content_hash=content_hash,
                        latency_ms=latency,
                        size_bytes=len(raw_bytes),
                        headers={"X-Agent-Reach-Backend": "yt-dlp", "X-Agent-Reach-Channel": "youtube"},
                        is_success=True,
                    )
                except Exception as parse_err:
                    logger.debug(f"yt-dlp JSON parse error: {parse_err}")

            return FetchResult(
                url=url,
                final_url=url,
                status_code=500,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                latency_ms=latency,
                is_success=False,
                error_message=proc.stderr[:300] or "yt-dlp failed to extract YouTube content.",
            )
        except Exception as exc:
            latency = (time.time() - start_time) * 1000.0
            return FetchResult(
                url=url,
                final_url=url,
                status_code=500,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                latency_ms=latency,
                is_success=False,
                error_message=str(exc),
            )

    def _fetch_rss(self, url: str, start_time: float) -> FetchResult:
        """Parse RSS/Atom feed using feedparser into structured markdown."""
        try:
            import feedparser
            feed = feedparser.parse(url)
            latency = (time.time() - start_time) * 1000.0

            title = feed.feed.get("title", "RSS Feed")
            desc = feed.feed.get("description", "")
            lines = [f"# {title}\n\n", f"{desc}\n\n", "## Entries\n\n"]

            for e in feed.entries[:15]:
                entry_title = e.get("title", "Untitled")
                entry_link = e.get("link", "")
                entry_summary = e.get("summary", "")
                lines.append(f"### {entry_title}\n- URL: {entry_link}\n- Summary: {entry_summary}\n\n")

            md_text = "".join(lines)
            is_suspicious, _ = ContentSanitizer.detect_prompt_injection(md_text)
            if is_suspicious:
                md_text = ContentSanitizer.sanitize_untrusted_text(md_text)

            raw_bytes = md_text.encode("utf-8")
            content_hash = compute_sha256(raw_bytes)

            return FetchResult(
                url=url,
                final_url=url,
                status_code=200,
                content_type="text/markdown; channel=rss",
                raw_content=raw_bytes,
                content_hash=content_hash,
                latency_ms=latency,
                size_bytes=len(raw_bytes),
                headers={"X-Agent-Reach-Backend": "feedparser", "X-Agent-Reach-Channel": "rss"},
                is_success=True,
            )
        except Exception as exc:
            latency = (time.time() - start_time) * 1000.0
            return FetchResult(
                url=url,
                final_url=url,
                status_code=500,
                content_type="text/plain",
                raw_content=b"",
                content_hash=compute_sha256(b""),
                latency_ms=latency,
                is_success=False,
                error_message=str(exc),
            )

    def _fetch_web_jina(
        self,
        url: str,
        timeout_seconds: int,
        limit_bytes: int,
        start_time: float,
    ) -> FetchResult:
        """
        Fetch arbitrary web page via Agent Reach's Jina Reader backend (https://r.jina.ai/).
        Falls back to standard HTTP fetch if Jina fails or rate limits.
        """
        jina_url = f"https://r.jina.ai/{url}"
        try:
            req = urllib.request.Request(
                jina_url,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "text/plain",
                    "X-No-Cache": "true",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                status_code = resp.getcode()
                raw_bytes = resp.read(limit_bytes + 1024)
                if len(raw_bytes) > limit_bytes:
                    raw_bytes = raw_bytes[:limit_bytes]

                text = raw_bytes.decode("utf-8", errors="replace")

                # Check anti-bot response
                if "title: attention required!" in text.lower() or "just a moment..." in text.lower():
                    raise RuntimeError("Jina Reader returned anti-bot challenge.")

                # Prompt injection screening
                is_suspicious, patterns = ContentSanitizer.detect_prompt_injection(text)
                if is_suspicious:
                    text = ContentSanitizer.sanitize_untrusted_text(text)
                    raw_bytes = text.encode("utf-8")

                latency = (time.time() - start_time) * 1000.0
                content_hash = compute_sha256(raw_bytes)

                return FetchResult(
                    url=url,
                    final_url=resp.geturl(),
                    status_code=status_code,
                    content_type="text/markdown",
                    raw_content=raw_bytes,
                    content_hash=content_hash,
                    latency_ms=latency,
                    size_bytes=len(raw_bytes),
                    headers={
                        "X-Agent-Reach-Backend": "jina_reader",
                        "X-Agent-Reach-Channel": "web",
                        "X-Defused-Injection": str(is_suspicious),
                    },
                    is_success=True,
                )
        except Exception as jina_err:
            logger.debug(f"Jina Reader fetch failed ({jina_err}). Falling back to standard WebFetcher.")

        # Fallback to direct HTTP fetch
        from src.internet.fetcher.fetcher import WebFetcher
        fetcher = WebFetcher(user_agent=self.user_agent, max_bytes=limit_bytes)
        res = fetcher.fetch(url, timeout_seconds=timeout_seconds, max_bytes=limit_bytes)
        if res.is_success and res.raw_content:
            # Check prompt injection on fallback
            text = res.raw_content.decode("utf-8", errors="replace")
            is_suspicious, _ = ContentSanitizer.detect_prompt_injection(text)
            if is_suspicious:
                text = ContentSanitizer.sanitize_untrusted_text(text)
                res.raw_content = text.encode("utf-8")
                res.content_hash = compute_sha256(res.raw_content)
                res.size_bytes = len(res.raw_content)
            res.headers["X-Agent-Reach-Backend"] = "direct_http_fallback"
            res.headers["X-Agent-Reach-Channel"] = "web"
        return res
