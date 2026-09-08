"""
Unit tests for Web Fetcher, Crawler, and Parsers.
"""

import unittest
from src.internet.fetcher.fetcher import WebFetcher
from src.internet.parsers.web_parser import WebContentParser
from src.internet.crawler.robots import RobotsPolicyManager
from src.internet.crawler.rate_limiter import DomainRateLimiter


class TestCrawlerAndFetcher(unittest.TestCase):

    def test_robots_policy_manager(self):
        robots = RobotsPolicyManager()
        # Default policy allows standard public pages
        allowed = robots.is_allowed("https://example.com/research")
        self.assertTrue(allowed)

    def test_domain_rate_limiter(self):
        limiter = DomainRateLimiter(default_interval_seconds=0.05)
        limiter.wait_if_needed("https://example.com/page1")
        limiter.wait_if_needed("https://example.com/page2")

    def test_html_content_parser(self):
        html_bytes = b"""
        <html>
            <head><title>AI Operating Model Research</title></head>
            <body>
                <main>
                    <h1>Enterprise AI Operating Model</h1>
                    <p>84% of surveyed organisations have not redesigned jobs to accommodate autonomous agents.</p>
                    <p>Straight-through routing alpha accounts for 37% of modeled EBITDA variance.</p>
                </main>
            </body>
        </html>
        """
        spans = WebContentParser.parse_html(html_bytes, "https://example.com/ai-report", "ai-report")
        self.assertGreaterEqual(len(spans), 2)
        self.assertIn("84%", spans[0].text)
        self.assertIn("alpha", spans[1].text)
        self.assertIsNotNone(spans[0].span_hash)


if __name__ == "__main__":
    unittest.main()
