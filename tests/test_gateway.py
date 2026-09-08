"""
Unit Tests for Model Gateway, OpenAI and Gemini Provider Adapters.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.gateway.base import ModelMessage
from src.gateway.gateway import ModelGateway
from src.gateway.provider_gemini import GeminiModelProvider
from src.gateway.provider_openai import OpenAIModelProvider
from src.gateway.mock_provider import MockModelProvider
from src.models.schemas import ModelResponse
from src.core.errors import ModelGatewayError


class TestModelGateway(unittest.TestCase):

    def setUp(self):
        self.gateway = ModelGateway(default_provider="mock")

    def test_mock_provider_generation(self):
        messages = [ModelMessage(role="user", content="Test query about operating model redesign.")]
        resp = self.gateway.generate(messages, provider_name="mock")
        self.assertEqual(resp.provider, "mock")
        self.assertGreater(len(resp.content), 0)
        self.assertGreater(resp.token_usage.total_tokens, 0)

    def test_openai_missing_key_raises_error(self):
        provider = OpenAIModelProvider(api_key=None)
        # Clear env var if present during test
        with patch.dict("os.environ", {}, clear=True):
            provider.api_key = None
            with self.assertRaises(ModelGatewayError):
                provider.generate([ModelMessage(role="user", content="Hello")])

    def test_gemini_missing_key_raises_error(self):
        provider = GeminiModelProvider(api_key=None)
        with patch.dict("os.environ", {}, clear=True):
            provider.api_key = None
            with self.assertRaises(ModelGatewayError):
                provider.generate([ModelMessage(role="user", content="Hello")])

    def test_gateway_fallback_to_mock_when_provider_fails(self):
        messages = [ModelMessage(role="user", content="Test query requiring fallback")]
        # When primary provider and all secondary fallbacks fail, gateway gracefully falls back to mock
        with patch.object(self.gateway.providers["gemini"], "generate", side_effect=ModelGatewayError("Simulated failure")), \
             patch.object(self.gateway.providers["omniroute"], "generate", side_effect=ModelGatewayError("OmniRoute offline")), \
             patch.object(self.gateway.providers["freellmapi"], "generate", side_effect=ModelGatewayError("FreeLLMAPI unavailable")), \
             patch.object(self.gateway.providers["openai"], "generate", side_effect=ModelGatewayError("OpenAI unavailable")):
            resp = self.gateway.generate(messages, provider_name="gemini")
            self.assertEqual(resp.provider, "mock")
            self.assertIn("mock", resp.model_name.lower())

    def test_openai_provider_mock_response(self):
        provider = OpenAIModelProvider(api_key="test-key")
        mock_http_response = MagicMock()
        mock_http_response.read.return_value = b'{"choices": [{"message": {"content": "OpenAI generated analysis."}}], "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}'
        mock_http_response.__enter__.return_value = mock_http_response

        with patch("urllib.request.urlopen", return_value=mock_http_response):
            with patch.dict("sys.modules", {"openai": None}):
                resp = provider.generate([ModelMessage(role="user", content="Analyze strategy")])
                self.assertEqual(resp.provider, "openai")
                self.assertEqual(resp.content, "OpenAI generated analysis.")
                self.assertEqual(resp.token_usage.total_tokens, 30)


if __name__ == "__main__":
    unittest.main()
