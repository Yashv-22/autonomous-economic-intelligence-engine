"""
Network Security & SSRF Protection Engine.
Enforces domain policies, prevents private subnet access, and canonicalizes URLs.
"""

import ipaddress
import socket
import urllib.parse
from typing import List, Optional
from src.core.config import settings
from src.core.errors import SecurityViolationError


class NetworkSecurityValidator:
    """Validates external URLs to prevent SSRF and policy violations."""

    def __init__(
        self,
        allowed_schemes: Optional[List[str]] = None,
        blocked_ip_ranges: Optional[List[str]] = None,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
    ):
        self.allowed_schemes = allowed_schemes or settings.security.allowed_schemes
        self.blocked_ip_ranges = [
            ipaddress.ip_network(cidr) for cidr in (blocked_ip_ranges or settings.security.blocked_ip_ranges)
        ]
        self.allowed_domains = allowed_domains or []
        self.blocked_domains = blocked_domains or ["localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal"]

    def validate_url(self, url: str) -> str:
        """
        Validate URL for scheme, domain policies, and SSRF vulnerabilities.
        Returns canonicalized URL if valid; raises SecurityViolationError otherwise.
        """
        if not url or not isinstance(url, str):
            raise SecurityViolationError("Empty or non-string URL provided")

        parsed = urllib.parse.urlparse(url.strip())

        # 1. Scheme Check
        if parsed.scheme.lower() not in self.allowed_schemes:
            raise SecurityViolationError(
                f"URL scheme '{parsed.scheme}' is prohibited. Allowed schemes: {self.allowed_schemes}"
            )

        hostname = parsed.hostname
        if not hostname:
            raise SecurityViolationError(f"Invalid URL missing hostname: {url}")

        hostname_lower = hostname.lower()

        # 2. Blocked Domains
        for blocked in self.blocked_domains:
            if hostname_lower == blocked or hostname_lower.endswith("." + blocked):
                raise SecurityViolationError(f"Access to blocked domain '{hostname}' is denied")

        # 3. Allowed Domains (if whitelist is active)
        if self.allowed_domains:
            domain_allowed = any(
                hostname_lower == allowed or hostname_lower.endswith("." + allowed)
                for allowed in self.allowed_domains
            )
            if not domain_allowed:
                raise SecurityViolationError(
                    f"Domain '{hostname}' is not in the authorized domain allowlist."
                )

        # 4. Strict SSRF IP Resolution Check
        if settings.security.enforce_strict_ssrf_check:
            self._check_ip_resolution(hostname)

        # Canonicalize URL (normalized query and path)
        canonical_url = urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path or "/",
            parsed.params,
            parsed.query,
            ""  # Strip fragment
        ))

        return canonical_url

    def _check_ip_resolution(self, hostname: str):
        """Resolve DNS and verify resolved IP is not within blocked/private subnets."""
        try:
            # Handle direct IP addresses
            ip_obj = ipaddress.ip_address(hostname)
            self._verify_ip(ip_obj)
            return
        except ValueError:
            pass  # Not a direct IP, proceed to DNS resolution

        try:
            # Resolve DNS addresses
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                self._verify_ip(ip_obj)
        except socket.gaierror as e:
            # DNS resolution failure
            raise SecurityViolationError(f"DNS resolution failed for host '{hostname}': {e}")

    def _verify_ip(self, ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address):
        """Check if IP falls into any forbidden subnet."""
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved:
            raise SecurityViolationError(
                f"SSRF violation: Access to private/loopback IP '{ip_obj}' is blocked."
            )

        for blocked_net in self.blocked_ip_ranges:
            if ip_obj in blocked_net:
                raise SecurityViolationError(
                    f"SSRF violation: IP '{ip_obj}' belongs to blocked subnet '{blocked_net}'."
                )


# Global default network validator
network_validator = NetworkSecurityValidator()
