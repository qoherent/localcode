"""Tests for logger module."""

import asyncio
import io
import sys
import unittest
from unittest.mock import patch


import logger


class TestLogger(unittest.TestCase):
    """Test structured logging functions."""

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_log_request_start(self, mock_stdout):
        """Test logging request_start event."""

        async def run_test():
            await logger.log_event(
                "request_start",
                {
                    "model": "glm-4.7-free",
                    "stream": False,
                    "messages_count": 1,
                    "has_tools": False,
                },
            )

        asyncio.run(run_test())

        output = mock_stdout.getvalue()
        self.assertIn("[REQUEST]", output)
        self.assertIn("Model: glm-4.7-free", output)
        self.assertIn("Stream: False", output)
        self.assertIn("Messages count: 1", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_log_request_with_tools(self, mock_stdout):
        """Test logging request with tool definitions."""

        async def run_test():
            await logger.log_event(
                "request_start",
                {
                    "model": "glm-4.7-free",
                    "stream": False,
                    "messages_count": 1,
                    "has_tools": True,
                    "tools_count": 2,
                },
            )

        asyncio.run(run_test())

        output = mock_stdout.getvalue()
        self.assertIn("[Tool Definitions] 2 tools", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_log_response_end(self, mock_stdout):
        """Test logging response_end event."""

        async def run_test():
            await logger.log_event(
                "response_end",
                {
                    "content": "Hello world",
                    "reasoning": None,
                    "tool_calls": None,
                    "finish_reason": "stop",
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    },
                },
            )

        asyncio.run(run_test())

        output = mock_stdout.getvalue()
        self.assertIn("[RESPONSE]", output)
        self.assertIn("Content: Hello world", output)
        self.assertIn("Finish reason: stop", output)
        self.assertIn("Usage - prompt: 10", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_log_response_with_reasoning(self, mock_stdout):
        """Test logging response with reasoning content."""

        async def run_test():
            await logger.log_event(
                "response_end",
                {
                    "content": "4",
                    "reasoning": "1+1=2, so 2+2=4",
                    "tool_calls": None,
                    "finish_reason": "stop",
                    "usage": {
                        "prompt_tokens": 7,
                        "completion_tokens": 1,
                        "total_tokens": 8,
                        "cached_tokens": 2,
                    },
                },
            )

        asyncio.run(run_test())

        output = mock_stdout.getvalue()
        self.assertIn("[Reasoning] 1+1=2, so 2+2=4", output)
        self.assertIn("[Cached Tokens: 2]", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_log_response_with_tool_call(self, mock_stdout):
        """Test logging response with tool call."""

        async def run_test():
            await logger.log_event(
                "response_end",
                {
                    "content": None,
                    "reasoning": None,
                    "tool_calls": [
                        {
                            "function": {"name": "get_time"},
                        }
                    ],
                    "finish_reason": "tool_calls",
                    "usage": {
                        "prompt_tokens": 50,
                        "completion_tokens": 20,
                        "total_tokens": 70,
                    },
                },
            )

        asyncio.run(run_test())

        output = mock_stdout.getvalue()
        self.assertIn("[Tool Call] get_time", output)
        self.assertIn("Finish reason: tool_calls", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_log_chunk_content(self, mock_stdout):
        """Test logging content chunk."""

        async def run_test():
            await logger.log_chunk("content", "Hello!")

        asyncio.run(run_test())

        output = mock_stdout.getvalue()
        self.assertIn("[STREAM CHUNK]", output)
        self.assertIn("Hello!", output)
        self.assertNotIn("[REASONING]", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_log_chunk_reasoning(self, mock_stdout):
        """Test logging reasoning chunk."""

        async def run_test():
            await logger.log_chunk("reasoning", "Let me think...")

        asyncio.run(run_test())

        output = mock_stdout.getvalue()
        self.assertIn("[STREAM CHUNK]", output)
        self.assertIn("[REASONING]", output)
        self.assertIn("Let me think...", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_log_chunk_tool_call(self, mock_stdout):
        """Test logging tool call chunk."""

        async def run_test():
            await logger.log_chunk("tool_call", "get_time")

        asyncio.run(run_test())

        output = mock_stdout.getvalue()
        self.assertIn("[STREAM CHUNK]", output)
        self.assertIn("[TOOL_CALL]", output)
        self.assertIn("get_time", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_content_truncation(self, mock_stdout):
        """Test that long content is truncated."""

        async def run_test():
            await logger.log_event(
                "response_end",
                {
                    "content": "x" * 200,
                    "reasoning": None,
                    "tool_calls": None,
                    "finish_reason": "stop",
                    "usage": {},
                },
            )

        asyncio.run(run_test())

        output = mock_stdout.getvalue()
        self.assertIn("...", output)
        self.assertEqual(
            len(output.split("Content: ")[1].split("\n")[0]), 153
        )  # "x"*150 + "..."

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_error_event(self, mock_stdout):
        """Test logging error event."""

        async def run_test():
            await logger.log_event(
                "error",
                {"message": "Connection failed"},
                level="ERROR",
            )

        asyncio.run(run_test())

        output = mock_stdout.getvalue()
        self.assertIn("[ERROR]", output)
        self.assertIn("Connection failed", output)


if __name__ == "__main__":
    unittest.main()
