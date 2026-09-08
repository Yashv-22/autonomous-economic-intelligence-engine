"""
Internet Search and Fetch Provider Abstractions.
Defines contracts for Live, Mock, and Replay Search and Content Retrieval.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str
    source_domain: str
    provider: str
    rank: int = 1
    published_date: Optional[str] = None
    source_type: str = "web"  # web, academic, corporate, government, news, blog
    relevance_score: float = 0.5
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FetchResult(BaseModel):
    url: str
    final_url: str
    status_code: int
    content_type: str
    raw_content: bytes
    content_hash: str
    headers: Dict[str, str] = Field(default_factory=dict)
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    latency_ms: float = 0.0
    size_bytes: int = 0
    is_success: bool = True
    error_message: Optional[str] = None


class BaseSearchProvider(ABC):
    """Abstract Base Class for Web Search Providers."""

    @abstractmethod
    def search(self, query: str, max_results: int = 10, **kwargs) -> List[SearchResultItem]:
        """Execute a search query and return ranked SearchResultItem list."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return unique provider identifier."""
        pass


class BaseFetchProvider(ABC):
    """Abstract Base Class for HTTP Content Fetching."""

    @abstractmethod
    def fetch(self, url: str, timeout_seconds: int = 10, max_bytes: int = 10_000_000) -> FetchResult:
        """Fetch raw bytes and metadata from URL."""
        pass
