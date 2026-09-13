from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ProviderLifecycleStatus(str, Enum):
    """Truthful tracking of provider lifecycle during an acquisition operation."""
    CONFIGURED = "configured"
    ELIGIBLE = "eligible"
    SELECTED = "selected"
    ATTEMPTED = "attempted"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    FALLBACK = "fallback"
    EXECUTED = "executed"


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
    is_mock: bool = False
    evidence_status: str = "LIVE"  # LIVE, MOCK, TEST_FIXTURE, REPLAY


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
    markdown: Optional[str] = None
    links: List[str] = Field(default_factory=list)
    structured_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    acquisition_provider: Optional[str] = None
    acquisition_method: Optional[str] = None
    is_mock: bool = False
    evidence_status: str = "LIVE"  # LIVE, MOCK, TEST_FIXTURE, REPLAY


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
    def fetch(self, url: str, timeout_seconds: float = 10, max_bytes: int = 10_000_000) -> FetchResult:
        """Fetch raw bytes and metadata from URL."""
        pass

    @property
    def provider_name(self) -> str:
        return "native_fetcher"


class BaseCrawlerProvider(ABC):
    """Abstract Base Class for recursive site traversal."""

    @abstractmethod
    def crawl(self, seed_url: str, max_depth: int = 2, max_pages: int = 10, **kwargs) -> List[FetchResult]:
        """Recursively crawl seed_url up to max_depth and max_pages."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


class BaseMapProvider(ABC):
    """Abstract Base Class for site topology and URL discovery."""

    @abstractmethod
    def map(self, url: str, search: Optional[str] = None, **kwargs) -> List[str]:
        """Discover URLs / sitemap for a root domain."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


class BaseBrowserProvider(ABC):
    """Abstract Base Class for dynamic JavaScript rendering and browser navigation."""

    @abstractmethod
    def render_dynamic(
        self,
        url: str,
        js_code: Optional[str] = None,
        wait_for: Optional[str] = None,
        timeout_seconds: float = 15.0,
        **kwargs,
    ) -> FetchResult:
        """Render page using headless browser with client-side JavaScript execution."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
