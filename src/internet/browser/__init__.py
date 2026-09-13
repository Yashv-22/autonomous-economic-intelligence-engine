"""
Browser Intelligence Fabric.
Defines browser automation interfaces and sandboxed adapters.
"""

from src.internet.browser.adapter import (
    BrowserSession,
    BrowserActionResult,
    BrowserProviderInterface,
)

__all__ = [
    "BrowserSession",
    "BrowserActionResult",
    "BrowserProviderInterface",
]
