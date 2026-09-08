"""
Mock and Replay Internet Providers.
Enables 100% deterministic offline unit testing and exact research session replay.
"""

import json
import os
from typing import List, Dict, Any, Optional

from src.internet.providers.base import BaseSearchProvider, BaseFetchProvider, SearchResultItem, FetchResult
from src.core.identifiers import compute_sha256


class MockSearchProvider(BaseSearchProvider):
    """Deterministic mock search provider with pre-seeded industry fixtures."""

    def __init__(self, fixtures: Optional[List[Dict[str, Any]]] = None):
        self._fixtures = fixtures or [
            {
                "title": "McKinsey QuantumBlack: The State of AI in 2026 - Generative AI Paradox",
                "url": "https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai-2026",
                "snippet": "88% of enterprises report regular use of generative AI, but only 22% report measurable EBIT impact at enterprise scale.",
                "source_domain": "mckinsey.com",
                "source_type": "consulting_research",
            },
            {
                "title": "BCG: Beyond the Pilot - Scaling AI Operating Models for 20% EBITDA Uplift",
                "url": "https://www.bcg.com/publications/2026/scaling-ai-operating-models-ebitda-uplift",
                "snippet": "The 10-20-70 rule governs AI transformation: 10% algorithms, 20% tech stack, 70% people and operating model redesign.",
                "source_domain": "bcg.com",
                "source_type": "consulting_research",
            },
            {
                "title": "Deloitte 2026 Human Capital Trends: Redesigning Work for AI Agents",
                "url": "https://www2.deloitte.com/us/en/insights/focus/human-capital-trends/2026/ai-agent-operating-model.html",
                "snippet": "84% of surveyed organisations have not redesigned core workflows despite deploying agentic automation.",
                "source_domain": "deloitte.com",
                "source_type": "consulting_research",
            },
            {
                "title": "Bain & Company: The Autonomous Agentic Operating Model",
                "url": "https://www.bain.com/insights/autonomous-agentic-operating-model-2026/",
                "snippet": "Organisational layers become obsolete; companies must transition from fixed hierarchies to dynamic agent meshes.",
                "source_domain": "bain.com",
                "source_type": "consulting_research",
            },
            {
                "title": "HBR: Why AI Coworkers Fail Without Explicit Governance",
                "url": "https://hbr.org/2026/03/why-ai-coworkers-fail-without-explicit-governance",
                "snippet": "Treating autonomous AI agents as 'coworkers' rather than bounded software services leads to severe accountability drift.",
                "source_domain": "hbr.org",
                "source_type": "expert_analysis",
            },
            {
                "title": "arXiv 2603.11942: Straight-Through Routing and Latency Bottlenecks in Enterprise AI",
                "url": "https://arxiv.org/abs/2603.11942",
                "snippet": "Mathematical proofs demonstrating that workflow value is dominated by the straight-through routing rate alpha.",
                "source_domain": "arxiv.org",
                "source_type": "academic",
            },
        ]

    @property
    def provider_name(self) -> str:
        return "mock"

    def search(self, query: str, max_results: int = 10, **kwargs) -> List[SearchResultItem]:
        query_tokens = set(query.lower().split())
        scored: List[tuple] = []

        for item in self._fixtures:
            text = f"{item['title']} {item['snippet']} {item['url']}".lower()
            overlap = sum(1 for token in query_tokens if token in text)
            score = overlap / max(len(query_tokens), 1)
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: List[SearchResultItem] = []
        for rank, (score, item) in enumerate(scored[:max_results], 1):
            results.append(
                SearchResultItem(
                    title=item["title"],
                    url=item["url"],
                    snippet=item["snippet"],
                    source_domain=item["source_domain"],
                    provider=self.provider_name,
                    rank=rank,
                    source_type=item.get("source_type", "web"),
                    relevance_score=max(0.2, score),
                )
            )
        return results


class ReplaySearchProvider(BaseSearchProvider):
    """Replay past recorded research sessions from a JSON trace file."""

    def __init__(self, trace_file_path: str):
        self.trace_file_path = trace_file_path
        self._records: Dict[str, List[Dict[str, Any]]] = {}
        if os.path.exists(trace_file_path):
            with open(trace_file_path, "r", encoding="utf-8") as f:
                self._records = json.load(f)

    @property
    def provider_name(self) -> str:
        return "replay"

    def search(self, query: str, max_results: int = 10, **kwargs) -> List[SearchResultItem]:
        query_key = query.strip().lower()
        if query_key in self._records:
            items = self._records[query_key]
            return [SearchResultItem(**it) for it in items[:max_results]]
        return []

    def record_query(self, query: str, results: List[SearchResultItem]):
        """Save a research query and its results to the trace file."""
        query_key = query.strip().lower()
        self._records[query_key] = [r.dict() for r in results]
        os.makedirs(os.path.dirname(os.path.abspath(self.trace_file_path)), exist_ok=True)
        with open(self.trace_file_path, "w", encoding="utf-8") as f:
            json.dump(self._records, f, indent=2)


class MockFetchProvider(BaseFetchProvider):
    """Deterministic mock fetch provider returning structured HTML/markdown for offline testing."""

    def __init__(self, fixtures: Optional[Dict[str, str]] = None):
        self._fixtures = fixtures or {
            "https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai-2026": (
                "<html><body><article>"
                "<h1>The State of AI in 2026: Generative AI Paradox</h1>"
                "<p>88% of enterprises report regular use of generative AI, but only 22% report measurable EBIT impact at enterprise scale.</p>"
                "<p>Organizations that capture value fundamentally redesign workflows rather than layering AI on legacy operating models.</p>"
                "</article></body></html>"
            ),
            "https://www.bcg.com/publications/2026/scaling-ai-operating-models-ebitda-uplift": (
                "<html><body><article>"
                "<h1>Scaling AI Operating Models for 20% EBITDA Uplift</h1>"
                "<p>The 10-20-70 rule governs AI transformation: 10% algorithms, 20% tech stack, 70% people and operating model redesign.</p>"
                "<p>Straight-through routing of transactions unlocks measurable EBITDA margin improvements across banking and tech.</p>"
                "</article></body></html>"
            ),
            "https://www2.deloitte.com/us/en/insights/focus/human-capital-trends/2026/ai-agent-operating-model.html": (
                "<html><body><article>"
                "<h1>Redesigning Work for AI Agents</h1>"
                "<p>84% of surveyed organisations have not redesigned core workflows despite deploying agentic automation.</p>"
                "<p>Agent governance requires structured oversight rather than treating autonomous models as passive coworkers.</p>"
                "</article></body></html>"
            ),
        }

    def fetch(self, url: str, timeout_seconds: int = 10, max_bytes: int = 10_000_000) -> FetchResult:
        content = self._fixtures.get(url)
        if not content:
            content = (
                f"<html><body><article>"
                f"<h1>Research Report: {url}</h1>"
                f"<p>Empirical evidence demonstrates that enterprise AI operating models require straight-through routing and governance redesign.</p>"
                f"<p>Organizations capturing value realize up to 20% EBITDA improvement by eliminating manual handoffs across cross-functional seams.</p>"
                f"</article></body></html>"
            )

        raw = content.encode("utf-8")
        h = compute_sha256(raw)
        return FetchResult(
            url=url,
            final_url=url,
            status_code=200,
            content_type="text/html",
            raw_content=raw,
            content_hash=h,
            headers={"Content-Type": "text/html", "X-Provider": "mock"},
            latency_ms=1.0,
            size_bytes=len(raw),
            is_success=True,
        )
