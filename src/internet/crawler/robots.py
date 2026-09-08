"""
Robots.txt Policy and Compliance Checker.
Parses domain robots.txt directives and enforces crawl rules.
"""

import urllib.request
import urllib.robotparser
from urllib.parse import urlparse
from typing import Dict, Optional

from src.core.logging import logger


class RobotsPolicyManager:
    """Manages cached robots.txt parsers per domain."""

    def __init__(self, user_agent: str = "ResearchBot"):
        self.user_agent = user_agent
        self._parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}

    def is_allowed(self, url: str) -> bool:
        """Check if URL fetching is allowed under domain robots.txt."""
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return True

        domain = parsed.netloc.lower()
        if domain not in self._parsers:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = f"{parsed.scheme}://{domain}/robots.txt"
            rp.set_url(robots_url)
            try:
                # Quick fetch with timeout
                req = urllib.request.Request(robots_url, headers={"User-Agent": self.user_agent})
                with urllib.request.urlopen(req, timeout=3) as res:
                    lines = res.read().decode("utf-8", errors="ignore").splitlines()
                    rp.parse(lines)
            except Exception:
                # If robots.txt is unavailable or 404, standard web practice permits crawling
                rp.allow_all = True
            self._parsers[domain] = rp

        parser = self._parsers[domain]
        try:
            return parser.can_fetch(self.user_agent, url)
        except Exception:
            return True
