"""
Unit Tests for FreeLLMAPI Model Provider Adapter and Gateway Routing.
"""

import os
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

from src.gateway.base import ModelMessage
from src.gateway.gateway import ModelGateway
from src.gateway.provider_freellmapi import FreeLLMAPIModelProvider
from src.core.errors import ModelGatewayError


class TestFreeLLMAPIModelProvider(unittest.TestCase):

    def setUp(self):
        self.provider = FreeLLMAPIModelProvider(
            base_url="http://127.0.0.1:3001/v1",
            api_key="sk-test-freellmapi-key",
            default_model="gemma-4-31b-it",
            timeout_seconds=5.0,
        )

    def test_provider_initialization(self):
        self.assertEqual(self.provider.name, "freellmapi")
        self.assertEqual(self.provider.base_url, "http://127.0.0.1:3001/v1")
        self.assertEqual(self.provider.api_key, "sk-test-freellmapi-key")
        self.assertEqual(self.provider.default_model, "gemma-4-31b-it")
        self.assertEqual(self.provider.timeout_seconds, 5.0)

    def test_auto_discover_unified_key_from_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_freeapi.db")
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT)")
            cursor.execute("INSERT INTO settings (key, value) VALUES ('unified_api_key', 'discovered-secret-key-123')")
            conn.commit()
            conn.close()

            with patch.dict(os.environ, {"FREELLMAPI_API_KEY": ""}, clear=False):
                # Also ensure empty string doesn't count
                provider = FreeLLMAPIModelProvider(
                    base_url="http://127.0.0.1:3001/v1",
                    api_key=None,
                    db_path=test_db,
                )
                self.assertEqual(provider.api_key, "discovered-secret-key-123")

    def test_missing_api_key_raises_error(self):
        provider = FreeLLMAPIModelProvider(
            base_url="http://127.0.0.1:3001/v1",
            api_key=None,
            db_path="nonexistent_db.sqlite",
        )
        # Ensure api_key is None
        provider.api_key = None

        messages = [ModelMessage(role="user", content="Hello")]
        with self.assertRaises(ModelGatewayError):
            provider.generate(messages)

        with self.assertRaises(ModelGatewayError):
            provider.list_models()

    def test_list_models_success(self):
        mock_response_data = {
            "data": [
                {"id": "gemma-4-31b-it", "object": "model", "owned_by": "google"},
                {"id": "llama-3.3-70b-versatile", "object": "model", "owned_by": "groq"},
            ]
        }
        mock_http = MagicMock()
        mock_http.status = 200
        mock_http.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_http.__enter__.return_value = mock_http

        with patch("urllib.request.urlopen", return_value=mock_http):
            models = self.provider.list_models()
            self.assertEqual(len(models), 2)
            self.assertEqual(models[0]["id"], "gemma-4-31b-it")
            self.assertTrue(self.provider.is_available())

    def test_list_models_http_error(self):
        mock_err = urllib.error.HTTPError(
            url="http://127.0.0.1:3001/v1/models",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=MagicMock(read=lambda: b'{"error": "Invalid unified API key"}'),
        )
        with patch("urllib.request.urlopen", side_effect=mock_err):
            with self.assertRaises(ModelGatewayError):
                self.provider.list_models()
            self.assertFalse(self.provider.is_available())

    def test_generate_success(self):
        mock_data = {
            "id": "chatcmpl-test-123",
            "object": "chat.completion",
            "model": "gemma-4-31b-it",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "FreeLLMAPI generated analysis on operating models.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 30,
                "total_tokens": 50,
            },
        }
        mock_http = MagicMock()
        mock_http.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_http.__enter__.return_value = mock_http

        messages = [ModelMessage(role="user", content="Analyze EBITDA margins")]
        with patch("urllib.request.urlopen", return_value=mock_http):
            resp = self.provider.generate(messages, model="gemma-4-31b-it")
            self.assertEqual(resp.provider, "freellmapi")
            self.assertEqual(resp.model_name, "gemma-4-31b-it")
            self.assertEqual(resp.content, "FreeLLMAPI generated analysis on operating models.")
            self.assertEqual(resp.token_usage.total_tokens, 50)
            self.assertEqual(resp.token_usage.estimated_cost_usd, 0.0)
            self.assertGreater(resp.latency_ms, 0)


class TestModelGatewayFreeLLMAPIIntegration(unittest.TestCase):

    def setUp(self):
        self.gateway = ModelGateway(default_provider="freellmapi")

    def test_gateway_has_freellmapi_registered(self):
        self.assertIn("freellmapi", self.gateway.providers)
        self.assertIsInstance(self.gateway.providers["freellmapi"], FreeLLMAPIModelProvider)

    def test_gateway_direct_generation_with_freellmapi(self):
        mock_data = {
            "model": "gemma-4-31b-it",
            "choices": [{"message": {"content": "Gateway routed through FreeLLMAPI."}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 18, "total_tokens": 30},
        }
        mock_http = MagicMock()
        mock_http.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_http.__enter__.return_value = mock_http

        # Ensure provider has an API key
        self.gateway.providers["freellmapi"].api_key = "test-key"

        messages = [ModelMessage(role="user", content="Test FreeLLMAPI Gateway")]
        with patch("urllib.request.urlopen", return_value=mock_http):
            resp = self.gateway.generate(messages, provider_name="freellmapi")
            self.assertEqual(resp.provider, "freellmapi")
            self.assertEqual(resp.content, "Gateway routed through FreeLLMAPI.")
            self.assertEqual(resp.token_usage.total_tokens, 30)

    def test_gateway_secondary_fallback_to_freellmapi_when_primary_fails(self):
        """When gemini fails, gateway falls back to freellmapi if configured."""
        mock_data = {
            "model": "gemma-4-31b-it",
            "choices": [{"message": {"content": "Secondary fallback to FreeLLMAPI succeeded."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
        }
        mock_http = MagicMock()
        mock_http.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_http.__enter__.return_value = mock_http

        self.gateway.providers["freellmapi"].api_key = "test-key"

        messages = [ModelMessage(role="user", content="Query with primary failure")]
        with patch.object(self.gateway.providers["gemini"], "generate", side_effect=ModelGatewayError("Gemini quota exceeded")):
            with patch.object(self.gateway.providers["omniroute"], "generate", side_effect=ModelGatewayError("OmniRoute offline")):
                with patch("urllib.request.urlopen", return_value=mock_http):
                    resp = self.gateway.generate(messages, provider_name="gemini")
                    self.assertEqual(resp.provider, "freellmapi")
                    self.assertEqual(resp.content, "Secondary fallback to FreeLLMAPI succeeded.")

    def test_gateway_fallback_to_mock_when_both_primary_and_freellmapi_fail(self):
        """When gemini and freellmapi both fail, gateway safely falls back to mock."""
        self.gateway.providers["freellmapi"].api_key = "test-key"

        messages = [ModelMessage(role="user", content="Query with complete failure")]
        with patch.object(self.gateway.providers["gemini"], "generate", side_effect=ModelGatewayError("Gemini error")), \
             patch.object(self.gateway.providers["omniroute"], "generate", side_effect=ModelGatewayError("OmniRoute offline")), \
             patch.object(self.gateway.providers["openai"], "generate", side_effect=ModelGatewayError("OpenAI offline")), \
             patch.object(self.gateway.providers["freellmapi"], "generate", side_effect=ModelGatewayError("FreeLLMAPI offline")):
            resp = self.gateway.generate(messages, provider_name="gemini")
            self.assertEqual(resp.provider, "mock")
            self.assertIn("mock", resp.model_name.lower())


if __name__ == "__main__":
    unittest.main()
