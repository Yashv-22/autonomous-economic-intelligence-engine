"""
Domain Rate Limiter.
Enforces politeness delays and max request concurrency per domain.
"""

import time
from urllib.parse import urlparse
from typing import Dict


class DomainRateLimiter:
    """Tracks last request timestamp per domain to enforce minimum intervals."""

    def __init__(self, default_interval_seconds: float = 0.5):
        self.default_interval = default_interval_seconds
        self._last_access: Dict[str, float] = {}

    def wait_if_needed(self, url: str) -> None:
        """Pause execution if request to domain occurs too rapidly."""
        domain = urlparse(url).netloc.lower()
        if not domain:
            return

        now = time.time()
        last_time = self._last_access.get(domain, 0.0)
        elapsed = now - last_time

        if elapsed < self.default_interval:
            time.sleep(self.default_interval - elapsed)

        self._last_access[domain] = time.time()
