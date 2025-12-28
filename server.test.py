"""Tests for server module."""

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import server


class TestServer(unittest.TestCase):
    """Test FastAPI server endpoints."""

    def setUp(self):
        """Set up mock dependencies."""
        self.mock_log_event = MagicMock()
        self.mock_post_chat_completions = AsyncMock()

        async def mock_post_gen(*args, **kwargs):
            yield {"type": "complete", "data": {"choices": []}}

        self.mock_post_chat_completions.return_value = mock_post_gen()

        self.mock_processor = {
            "extract_request_info": lambda req: {
                "model": "test",
                "stream": False,
                "messages_count": 1,
                "has_tools": False,
                "tools_count": 0,
            },
            "extract_message_parts": lambda msg: (msg.get("content"), None, None),
            "extract_usage_stats": lambda resp: {
                "prompt_tokens": 5,
                "completion_tokens": 1,
                "total_tokens": 6,
            },
            "get_finish_reason": lambda resp: "stop",
            "categorize_delta": lambda delta: "content",
        }

        self.app = server.create_app(
            backend_url="http://test",
            log_event=self.mock_log_event,
            post_chat_completions=self.mock_post_chat_completions,
            processor=self.mock_processor,
        )

    async def test_health_endpoint(self):
        """Test /health endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(self.app)
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["provider"], "LocalCode Middleware")
        self.assertEqual(data["backend_url"], "http://test")

    async def test_chat_completions_non_stream(self):
        """Test POST /v1/chat/completions (non-streaming)."""
        from fastapi.testclient import TestClient

        async def mock_post_gen(*args, **kwargs):
            yield {
                "type": "complete",
                "data": {
                    "choices": [
                        {
                            "message": {"content": "Hello!"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 5,
                        "completion_tokens": 1,
                        "total_tokens": 6,
                    },
                },
            }

        self.mock_post_chat_completions.return_value = mock_post_gen()

        client = TestClient(self.app)
        response = client.post(
            "/v1/chat/completions",
            json={"model": "test", "messages": [{"role": "user", "content": "Hi"}]},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("choices", data)
        self.assertEqual(data["choices"][0]["message"]["content"], "Hello!")

        self.mock_log_event.assert_any_call(
            "request_start",
            {
                "model": "test",
                "stream": False,
                "messages_count": 1,
                "has_tools": False,
                "tools_count": 0,
            },
        )

    async def test_chat_completions_streaming(self):
        """Test POST /v1/chat/completions (streaming)."""
        from fastapi.testclient import TestClient

        async def mock_post_gen(*args, **kwargs):
            yield {"type": "chunk", "data": {"choices": [{"delta": {"content": "Hi"}}]}}
            yield {"type": "chunk", "data": {"choices": [{"delta": {"content": "!"}}]}}
            yield {"type": "done"}

        self.mock_post_chat_completions.return_value = mock_post_gen()

        client = TestClient(self.app)
        response = client.post(
            "/v1/chat/completions",
            json={"model": "test", "messages": [], "stream": True},
        )

        self.assertEqual(response.status_code, 200)

        body = b"".join(response.body_iterator)
        lines = body.decode("utf-8").split("\n")

        data_lines = [l for l in lines if l.startswith("data: ")]
        self.assertEqual(len(data_lines), 3)

    async def test_chat_completions_with_reasoning(self):
        """Test handling reasoning content."""
        from fastapi.testclient import TestClient

        async def mock_post_gen(*args, **kwargs):
            yield {
                "type": "complete",
                "data": {
                    "choices": [
                        {
                            "message": {
                                "content": "4",
                                "reasoning_content": "1+1=2, so 2+2=4",
                            },
                            "finish_reason": "stop",
                        }
                    ]
                },
            }

        self.mock_post_chat_completions.return_value = mock_post_gen()

        client = TestClient(self.app)
        response = client.post(
            "/v1/chat/completions",
            json={"model": "test", "messages": []},
        )

        self.assertEqual(response.status_code, 200)

        self.mock_log_event.assert_any_call(
            "response_end",
            {
                "content": "4",
                "reasoning": "1+1=2, so 2+2=4",
                "tool_calls": None,
                "finish_reason": "stop",
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 1,
                    "total_tokens": 6,
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
