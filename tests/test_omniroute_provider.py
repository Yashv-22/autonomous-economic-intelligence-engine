"""
Unit Tests for OmniRoute Model Provider Adapter and Capability-Aware Routing.
Enforces zero SQLite coupling, decoupled environment configuration, and task capability tiers.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

from src.gateway.base import ModelMessage
from src.gateway.gateway import ModelGateway, TaskCapability
from src.gateway.provider_omniroute import OmniRouteModelProvider
from src.core.errors import ModelGatewayError


class TestOmniRouteModelProvider(unittest.TestCase):

    def setUp(self):
        self.provider = OmniRouteModelProvider(
            base_url="http://127.0.0.1:20128/v1",
            api_key="sk-test-omniroute-key",
            default_model="research-general",
            timeout_seconds=5.0,
        )

    def test_provider_initialization(self):
        self.assertEqual(self.provider.name, "omniroute")
        self.assertEqual(self.provider.base_url, "http://127.0.0.1:20128/v1")
        self.assertEqual(self.provider.api_key, "sk-test-omniroute-key")
        self.assertEqual(self.provider.default_model, "research-general")
        self.assertEqual(self.provider.timeout_seconds, 5.0)

    def test_zero_sqlite_coupling(self):
        """Verify that provider does not attempt to access or query internal storage.sqlite."""
        with patch.dict(os.environ, {"OMNIROUTE_API_KEY": "env-configured-key-999"}, clear=False):
            prov = OmniRouteModelProvider(base_url="http://127.0.0.1:20128/v1")
            self.assertEqual(prov.api_key, "env-configured-key-999")
            self.assertFalse(hasattr(prov, "db_path"))

    def test_missing_api_key_raises_error(self):
        prov = OmniRouteModelProvider(
            base_url="http://127.0.0.1:20128/v1",
            api_key=None,
        )
        prov.api_key = None

        messages = [ModelMessage(role="user", content="Hello")]
        with self.assertRaises(ModelGatewayError):
            prov.generate(messages)

        with self.assertRaises(ModelGatewayError):
            prov.list_models()

        self.assertFalse(prov.is_available())

    def test_list_models_success(self):
        mock_response_data = {
            "data": [
                {"id": "research-reasoning", "object": "model"},
                {"id": "research-fast", "object": "model"},
                {"id": "research-general", "object": "model"},
            ]
        }
        mock_http = MagicMock()
        mock_http.status = 200
        mock_http.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_http.__enter__.return_value = mock_http

        with patch("urllib.request.urlopen", return_value=mock_http):
            models = self.provider.list_models()
            self.assertEqual(len(models), 3)
            self.assertEqual(models[0]["id"], "research-reasoning")
            self.assertTrue(self.provider.is_available())

    def test_generate_chat_completion_success(self):
        mock_response_data = {
            "id": "chatcmpl-test-123",
            "model": "research-reasoning",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Autonomous economic analysis complete.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 40,
                "completion_tokens": 12,
                "total_tokens": 52,
            },
        }

        mock_http = MagicMock()
        mock_http.status = 200
        mock_http.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_http.__enter__.return_value = mock_http

        messages = [
            ModelMessage(role="system", content="You are an economic reasoning engine."),
            ModelMessage(role="user", content="Analyze market problem PROB-001"),
        ]

        with patch("urllib.request.urlopen", return_value=mock_http) as mock_urlopen:
            resp = self.provider.generate(messages=messages, model="research-reasoning")
            self.assertEqual(resp.content, "Autonomous economic analysis complete.")
            self.assertEqual(resp.model_name, "research-reasoning")
            self.assertEqual(resp.provider, "omniroute")
            self.assertEqual(resp.token_usage.total_tokens, 52)
            self.assertGreaterEqual(resp.latency_ms, 0)

            # Verify Bearer token was set in headers
            req_arg = mock_urlopen.call_args[0][0]
            self.assertEqual(req_arg.headers["Authorization"], "Bearer sk-test-omniroute-key")

    def test_capability_aware_model_resolution(self):
        gateway = ModelGateway()

        fast_model = gateway.resolve_model_for_capability("omniroute", TaskCapability.FAST)
        self.assertEqual(fast_model, "auto/best-fast")

        reasoning_model = gateway.resolve_model_for_capability("omniroute", TaskCapability.REASONING)
        self.assertEqual(reasoning_model, "auto/best-chat")

        econ_model = gateway.resolve_model_for_capability("omniroute", TaskCapability.ECONOMIC_REASONING)
        self.assertEqual(econ_model, "auto/best-reasoning")


if __name__ == "__main__":
    unittest.main()
