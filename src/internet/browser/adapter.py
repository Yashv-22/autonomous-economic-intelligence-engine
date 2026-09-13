"""
Browser Automation and Navigation Abstraction.
Defines interfaces for safe, sandbox-enforced headless browser navigation and extraction.
Strictly prohibits arbitrary shell execution (bashExec), local code compilation, or filesystem access.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.internet.providers.base import FetchResult
from src.core.identifiers import compute_sha256, generate_prefixed_id
from src.security.network import network_validator
from src.core.errors import SecurityViolationError


class BrowserActionResult(BaseModel):
    """Result of a single browser interaction step."""
    action_type: str  # navigate, click, scroll, wait, extract_dom
    target: str
    status: str = "success"  # success, failed, blocked
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    extracted_text: Optional[str] = None
    screenshot_b64: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BrowserSession(BaseModel):
    """Metadata tracking an active sandboxed browser session."""
    session_id: str
    initial_url: str
    current_url: str
    is_active: bool = True
    actions_executed: List[BrowserActionResult] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BrowserProviderInterface(ABC):
    """
    Standard interface for browser automation providers.
    Enforces SSRF prevention and prevents local shell execution.
    """

    @abstractmethod
    def navigate(self, url: str, wait_for_selector: Optional[str] = None, timeout_seconds: float = 15.0) -> FetchResult:
        """Navigate to URL and return rendered DOM/Markdown."""
        pass

    @abstractmethod
    def execute_action(
        self,
        session_id: str,
        action_type: str,
        target_selector: str,
        value: Optional[str] = None,
    ) -> BrowserActionResult:
        """Execute safe interaction step (click, scroll, type) on an active page."""
        pass
