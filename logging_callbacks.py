"""Custom logging callbacks for LocalCode-style event logging.

This module provides LiteLLM-compatible callbacks that produce the same
structured output as our original custom middleware implementation.

Usage:
    import logging_callbacks  # Auto-registers on import
"""

import time
from typing import Any, Optional

import litellm
from litellm.integrations.custom_logger import CustomLogger


def get_timestamp() -> str:
    """Get current time as HH:MM:SS string."""
    return time.strftime("%H:%M:%S")


class LocalCodeLogger(CustomLogger):
    """Custom logger for LiteLLM proxy that produces LocalCode-style output."""

    def log_pre_api_call(self, model: str, messages: list, kwargs: dict) -> None:
        """Called before each API call."""
        print(f"\n{'=' * 80}")
        print(f"[REQUEST] {get_timestamp()}")

        print(f"Model: {model}")

        stream = kwargs.get("stream", False)
        print(f"Stream: {stream}")

        print(f"Messages count: {len(messages)}")

        tools = kwargs.get("tools", [])
        if tools:
            print(f"[Tool Definitions] {len(tools)} tools")

        print(f"{'=' * 80}\n")

    def log_post_api_call(
        self, kwargs: dict, response_obj: dict, start_time: Any, end_time: Any
    ) -> None:
        """Called after each API call."""
        pass

    def log_success_event(
        self, kwargs: dict, response_obj: dict, start_time: Any, end_time: Any
    ) -> None:
        """Called on successful response."""
        print(f"\n{'-' * 80}")
        print(f"[RESPONSE] {get_timestamp()}")

        model = kwargs.get("model", "unknown")
        print(f"Model: {model}")

        choices = response_obj.get("choices", [])
        if choices:
            choice = choices[0]
            message = choice.get("message", {})

            content = message.get("content", "")
            if content:
                preview = content[:150] + "..." if len(content) > 150 else content
                print(f"Content: {preview}")

            reasoning = message.get("reasoning_content", "")
            if reasoning:
                preview = reasoning[:150] + "..." if len(reasoning) > 150 else reasoning
                print(f"[Reasoning] {preview}")

            finish_reason = choice.get("finish_reason", "unknown")
            print(f"Finish reason: {finish_reason}")

        usage = response_obj.get("usage", {})
        if usage:
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            print(
                f"Usage - prompt: {prompt_tokens}, completion: {completion_tokens}, total: {total_tokens}"
            )

        print(f"{'-' * 80}\n")

    def log_failure_event(
        self, kwargs: dict, response_obj: dict, start_time: Any, end_time: Any
    ) -> None:
        """Called on failed response."""
        print(f"\n{'X' * 80}")
        print(f"[ERROR] {get_timestamp()}")

        exception_event = kwargs.get("exception", None)
        if exception_event:
            print(
                f"Exception: {type(exception_event).__name__}: {str(exception_event)}"
            )

        model = kwargs.get("model", "unknown")
        print(f"Model: {model}")

        print(f"{'X' * 80}\n")

    async def async_log_success_event(
        self, kwargs: dict, response_obj: dict, start_time: Any, end_time: Any
    ) -> None:
        """Async version of success logging."""
        self.log_success_event(kwargs, response_obj, start_time, end_time)

    async def async_log_failure_event(
        self, kwargs: dict, response_obj: dict, start_time: Any, end_time: Any
    ) -> None:
        """Async version of failure logging."""
        self.log_failure_event(kwargs, response_obj, start_time, end_time)


_localcode_logger = LocalCodeLogger()
litellm.callbacks = [_localcode_logger]
