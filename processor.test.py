"""Tests for processor module."""

import unittest

import processor


class TestProcessor(unittest.TestCase):
    """Test request/response processing functions."""

    def test_extract_request_info_basic(self):
        """Test extracting basic request info."""
        request = {
            "model": "glm-4.7-free",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        }

        info = processor.extract_request_info(request)

        self.assertEqual(info["model"], "glm-4.7-free")
        self.assertEqual(info["messages_count"], 1)
        self.assertEqual(info["stream"], False)
        self.assertFalse(info["has_tools"])
        self.assertEqual(info["tools_count"], 0)

    def test_extract_request_info_with_tools(self):
        """Test extracting request info with tools."""
        request = {
            "model": "glm-4.7-free",
            "messages": [{"role": "user", "content": "Edit file"}],
            "stream": False,
            "tools": [
                {"type": "function", "function": {"name": "edit"}},
                {"type": "function", "function": {"name": "read"}},
            ],
        }

        info = processor.extract_request_info(request)

        self.assertTrue(info["has_tools"])
        self.assertEqual(info["tools_count"], 2)

    def test_extract_request_info_default_values(self):
        """Test extracting request info with missing fields."""
        request = {}

        info = processor.extract_request_info(request)

        self.assertEqual(info["model"], "unknown")
        self.assertEqual(info["messages_count"], 0)
        self.assertFalse(info["stream"])
        self.assertFalse(info["has_tools"])

    def test_extract_message_parts_regular(self):
        """Test extracting message parts from regular message."""
        message = {"content": "Hello world!"}

        content, reasoning, tool_calls = processor.extract_message_parts(message)

        self.assertEqual(content, "Hello world!")
        self.assertIsNone(reasoning)
        self.assertIsNone(tool_calls)

    def test_extract_message_parts_with_reasoning(self):
        """Test extracting message parts with reasoning."""
        message = {
            "content": "4",
            "reasoning_content": "1+1=2, so 2+2=4",
        }

        content, reasoning, tool_calls = processor.extract_message_parts(message)

        self.assertEqual(content, "4")
        self.assertEqual(reasoning, "1+1=2, so 2+2=4")
        self.assertIsNone(tool_calls)

    def test_extract_message_parts_with_tool_call(self):
        """Test extracting message parts with tool call."""
        message = {
            "tool_calls": [
                {
                    "function": {
                        "name": "edit",
                        "arguments": '{"path": "/tmp/file"}',
                    }
                }
            ]
        }

        content, reasoning, tool_calls = processor.extract_message_parts(message)

        self.assertIsNone(content)
        self.assertIsNone(reasoning)
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["function"]["name"], "edit")

    def test_extract_message_parts_empty(self):
        """Test extracting from empty message."""
        message = {}

        content, reasoning, tool_calls = processor.extract_message_parts(message)

        self.assertIsNone(content)
        self.assertIsNone(reasoning)
        self.assertIsNone(tool_calls)

    def test_extract_usage_stats_basic(self):
        """Test extracting usage stats."""
        response = {
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 10,
                "total_tokens": 60,
            }
        }

        usage = processor.extract_usage_stats(response)

        self.assertEqual(usage["prompt_tokens"], 50)
        self.assertEqual(usage["completion_tokens"], 10)
        self.assertEqual(usage["total_tokens"], 60)
        self.assertIsNone(usage["cached_tokens"])

    def test_extract_usage_stats_with_cache(self):
        """Test extracting usage stats with cached tokens."""
        response = {
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 10,
                "total_tokens": 60,
                "prompt_tokens_details": {"cached_tokens": 12},
            }
        }

        usage = processor.extract_usage_stats(response)

        self.assertEqual(usage["cached_tokens"], 12)

    def test_extract_usage_stats_missing(self):
        """Test extracting usage stats with missing usage field."""
        response = {}

        usage = processor.extract_usage_stats(response)

        self.assertEqual(usage["prompt_tokens"], 0)
        self.assertEqual(usage["completion_tokens"], 0)
        self.assertEqual(usage["total_tokens"], 0)

    def test_categorize_delta_content(self):
        """Test categorizing content delta."""
        self.assertEqual(processor.categorize_delta({"content": "Hello"}), "content")

    def test_categorize_delta_reasoning(self):
        """Test categorizing reasoning delta."""
        self.assertEqual(
            processor.categorize_delta({"reasoning_content": "thinking..."}),
            "reasoning",
        )

    def test_categorize_delta_tool_call(self):
        """Test categorizing tool call delta."""
        self.assertEqual(processor.categorize_delta({"tool_calls": []}), "tool_call")

    def test_categorize_delta_empty(self):
        """Test categorizing empty delta."""
        self.assertEqual(processor.categorize_delta({}), "none")

    def test_categorize_delta_priority(self):
        """Test that tool_calls has priority over reasoning."""
        delta = {
            "tool_calls": [],
            "reasoning_content": "thinking...",
            "content": "Hello",
        }

        self.assertEqual(processor.categorize_delta(delta), "tool_call")

    def test_get_finish_reason(self):
        """Test extracting finish reason."""
        response = {"choices": [{"finish_reason": "stop"}]}

        self.assertEqual(processor.get_finish_reason(response), "stop")

    def test_get_finish_reason_missing_choices(self):
        """Test finish reason with missing choices."""
        response = {}

        self.assertEqual(processor.get_finish_reason(response), "unknown")

    def test_get_finish_reason_missing_reason(self):
        """Test finish reason with missing finish_reason field."""
        response = {"choices": [{"index": 0}]}

        self.assertEqual(processor.get_finish_reason(response), "unknown")


if __name__ == "__main__":
    unittest.main()
