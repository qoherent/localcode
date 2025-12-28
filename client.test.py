"""Tests for client module."""

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import client


class TestClient(unittest.TestCase):
    """Test OpenAI-compatible client functions."""

    @patch("httpx.AsyncClient")
    async def test_fetch_models_zen_format(self, mock_client_class):
        """Test fetching models from zen format."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [
                {"id": "glm-4.7-free"},
                {"id": "claude-sonnet-4"},
            ],
        }
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        models = await client.fetch_models("https://opencode.ai/zen/v1")

        self.assertEqual(len(models), 2)
        self.assertIn("glm-4.7-free", models)
        self.assertIn("claude-sonnet-4", models)

    @patch("httpx.AsyncClient")
    async def test_fetch_models_llama_format(self, mock_client_class):
        """Test fetching models from llama.cpp format."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": "gpt-3.5-turbo"},
            {"id": "llama-2-7b"},
        ]
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        models = await client.fetch_models("http://localhost:8080/v1")

        self.assertEqual(len(models), 2)
        self.assertIn("gpt-3.5-turbo", models)
        self.assertIn("llama-2-7b", models)

    @patch("httpx.AsyncClient")
    async def test_fetch_models_unknown_format(self, mock_client_class):
        """Test fetching models from unknown format."""
        mock_response = MagicMock()
        mock_response.json.return_value = ["model-1", "model-2"]
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        models = await client.fetch_models("http://unknown.com/v1")

        self.assertEqual(len(models), 2)

    async def test_select_free_model_zen(self):
        """Test selecting free model from zen."""
        with patch("client.fetch_models") as mock_fetch:
            mock_fetch.return_value = [
                "claude-sonnet-4",
                "glm-4.7-free",
                "big-pickle",
            ]

            selected = await client.select_free_model("https://opencode.ai/zen/v1")

            self.assertEqual(selected, "glm-4.7-free")

    async def test_select_free_model_no_known_free(self):
        """Test selecting model when no known free models."""
        with patch("client.fetch_models") as mock_fetch:
            mock_fetch.return_value = ["custom-model", "other-model"]

            selected = await client.select_free_model("https://opencode.ai/zen/v1")

            self.assertEqual(selected, "custom-model")

    async def test_select_free_model_no_models(self):
        """Test selecting model when no models available."""
        with patch("client.fetch_models") as mock_fetch:
            mock_fetch.return_value = []

            with self.assertRaises(RuntimeError):
                await client.select_free_model("https://opencode.ai/zen/v1")

    @patch("httpx.AsyncClient")
    async def test_post_chat_completions_non_stream(self, mock_client_class):
        """Test POST to chat completions (non-streaming)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "total_tokens": 10},
        }
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        events = []
        request = {
            "model": "glm-4.7-free",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        }

        async for event in client.post_chat_completions(
            request, "https://opencode.ai/zen/v1"
        ):
            events.append(event)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "complete")
        self.assertIn("choices", events[0]["data"])

    @patch("httpx.AsyncClient")
    async def test_post_chat_completions_streaming(self, mock_client_class):
        """Test POST to chat completions (streaming)."""
        mock_response = MagicMock()

        chunks = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":" world"}}]}\n\n',
            b"data: [DONE]\n\n",
        ]
        chunk_index = 0

        async def mock_aiter_bytes():
            nonlocal chunk_index
            for chunk in chunks:
                yield chunk
                chunk_index += 1

        mock_response.aiter_bytes = mock_aiter_bytes
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.json.return_value = {"result": "ok"}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.stream = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        events = []
        request = {
            "model": "glm-4.7-free",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        }

        async for event in client.post_chat_completions(
            request, "https://opencode.ai/zen/v1"
        ):
            events.append(event)

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]["type"], "chunk")
        self.assertEqual(events[1]["type"], "chunk")
        self.assertEqual(events[2]["type"], "done")

    @patch("httpx.AsyncClient")
    async def test_post_with_api_key(self, mock_client_class):
        """Test POST with API key."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": []}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        request = {"model": "test", "messages": [], "stream": False}

        async for _ in client.post_chat_completions(
            request, "http://localhost:8080/v1", api_key="test-key"
        ):
            break

        args, kwargs = mock_client.post.call_args
        headers = kwargs.get("headers", args[1].get("headers", {}))

        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer test-key")


if __name__ == "__main__":
    unittest.main()
