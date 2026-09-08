"""
Unit Tests for Controlled Tool Layer & Permission Gating.
"""

import unittest
from src.tools.base import BaseTool
from src.tools.registry import ToolRegistry
from src.tools.search_tool import SearchTool
from src.tools.fetch_tool import FetchTool
from src.tools.extract_tool import ExtractTool
from src.models.schemas import ToolPermission
from src.internet.search.engine import MultiProviderSearchEngine
from src.internet.providers.mock_provider import MockSearchProvider
from src.core.errors import SecurityViolationError, ToolExecutionError


class DummyHighRiskTool(BaseTool):
    name: str = "danger_action"
    description: str = "High risk operation."
    permission_level: ToolPermission = ToolPermission.HIGH_RISK

    def run(self, **kwargs):
        return "HIGH_RISK_EXECUTED"


class TestToolLayer(unittest.TestCase):

    def setUp(self):
        self.registry = ToolRegistry()
        mock_engine = MultiProviderSearchEngine(providers=[MockSearchProvider()])
        self.search_tool = SearchTool(search_engine=mock_engine)
        self.fetch_tool = FetchTool(mock_web_index={
            "https://example.com/test-article": "<html><body><h1>Title</h1><p>This is a mock research article about operating models.</p></body></html>"
        })
        self.extract_tool = ExtractTool()
        self.danger_tool = DummyHighRiskTool()

        self.registry.register_tool(self.search_tool)
        self.registry.register_tool(self.fetch_tool)
        self.registry.register_tool(self.extract_tool)
        self.registry.register_tool(self.danger_tool)

    def test_permission_enforcement_blocks_unauthorized_call(self):
        """Verify caller with READ_ONLY permission cannot invoke HIGH_RISK tool."""
        with self.assertRaises(SecurityViolationError):
            self.registry.invoke_tool(
                "danger_action",
                caller_permission=ToolPermission.READ_ONLY,
            )

    def test_permission_enforcement_allows_authorized_call(self):
        """Verify caller with HIGH_RISK permission can invoke HIGH_RISK tool."""
        res = self.registry.invoke_tool(
            "danger_action",
            caller_permission=ToolPermission.HIGH_RISK,
        )
        self.assertTrue(res.success)
        self.assertEqual(res.output, "HIGH_RISK_EXECUTED")

    def test_search_tool_discovery(self):
        """Verify search tool returns relevant ranked results."""
        res = self.registry.invoke_tool(
            "search_sources",
            caller_permission=ToolPermission.READ_ONLY,
            query="ai adoption ebitda",
            max_results=3,
        )
        self.assertTrue(res.success)
        self.assertGreater(len(res.output), 0)
        self.assertIn("url", res.output[0])
        self.assertTrue(any(domain in res.output[0]["url"] for domain in ["mckinsey.com", "bcg.com", "bain.com", "arxiv.org"]))

    def test_fetch_tool_mock_acquisition(self):
        """Verify fetch tool retrieves and hashes mock web content safely."""
        res = self.registry.invoke_tool(
            "fetch_web_content",
            caller_permission=ToolPermission.READ_ONLY,
            url="https://example.com/test-article",
        )
        self.assertTrue(res.success)
        self.assertEqual(res.output["domain"], "example.com")
        self.assertTrue(res.output["is_mock"])
        self.assertEqual(len(res.output["document_hash"]), 64)

    def test_extract_tool_span_generation(self):
        """Verify extract tool creates sanitized SourceSpans from HTML."""
        html_content = "<html><body><p>Accelerating task velocity with AI causes downstream queue drift.</p></body></html>"
        res = self.registry.invoke_tool(
            "extract_spans",
            caller_permission=ToolPermission.READ_ONLY,
            raw_content=html_content,
            document_name="test_doc",
            document_hash="111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000",
            is_html=True,
        )
        self.assertTrue(res.success)
        spans = res.output
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].document_name, "test_doc")
        self.assertEqual(len(spans[0].span_hash), 64)


if __name__ == "__main__":
    unittest.main()
