"""Structured event logging for LocalCode Middleware."""

import time
from typing import Any, Dict, Literal


EventType = Literal[
    "request_start",
    "response_end",
    "stream_chunk",
    "tool_call",
    "reasoning",
    "error",
    "usage",
]


def get_timestamp() -> str:
    """Get current time as HH:MM:SS string."""
    return time.strftime("%H:%M:%S")


async def log_event(
    event_type: EventType,
    data: Dict[str, Any],
    level: Literal["DEBUG", "INFO", "WARN", "ERROR"] = "INFO",
) -> None:
    """Emit structured log event.

    Args:
        event_type: Type of event (request_start, response_end, etc.)
        data: Event data as dictionary
        level: Log level
    """
    ts = get_timestamp()

    match event_type:
        case "request_start":
            print(f"\n{'=' * 80}")
            print(f"[REQUEST] {ts}")
            print(f"Model: {data.get('model', 'unknown')}")
            print(f"Stream: {data.get('stream', False)}")
            print(f"Messages count: {data.get('messages_count', 0)}")
            if data.get("has_tools"):
                print(f"[Tool Definitions] {data.get('tools_count', 0)} tools")
            print(f"{'=' * 80}\n")

        case "response_end":
            print(f"\n{'-' * 80}")
            print(f"[RESPONSE] {ts}")
            content = data.get("content")
            if content:
                preview = content[:150] + "..." if len(content) > 150 else content
                print(f"Content: {preview}")

            reasoning = data.get("reasoning")
            if reasoning:
                preview = reasoning[:150] + "..." if len(reasoning) > 150 else reasoning
                print(f"[Reasoning] {preview}")

            tool_calls = data.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    func_name = tc.get("function", {}).get("name", "unknown")
                    print(f"[Tool Call] {func_name}")

            finish_reason = data.get("finish_reason", "unknown")
            print(f"Finish reason: {finish_reason}")

            usage = data.get("usage", {})
            if usage:
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                cached_tokens = usage.get("cached_tokens")

                print(
                    f"Usage - prompt: {prompt_tokens}, "
                    f"completion: {completion_tokens}, "
                    f"total: {total_tokens}"
                )

                if cached_tokens:
                    print(f"[Cached Tokens: {cached_tokens}]")

            print(f"{'-' * 80}\n")

        case "tool_call":
            func_name = data.get("function_name", "unknown")
            print(f"[Tool Call] {func_name}")

        case "reasoning":
            reasoning_content = data.get("content", "")
            if reasoning_content:
                preview = (
                    reasoning_content[:150] + "..."
                    if len(reasoning_content) > 150
                    else reasoning_content
                )
                print(f"[Reasoning] {preview}")

        case "error":
            message = data.get("message", "Unknown error")
            print(f"[ERROR] {ts} {message}")

        case "usage":
            prompt_tokens = data.get("prompt_tokens", 0)
            completion_tokens = data.get("completion_tokens", 0)
            total_tokens = data.get("total_tokens", 0)
            cached_tokens = data.get("cached_tokens")

            print(
                f"Usage - prompt: {prompt_tokens}, "
                f"completion: {completion_tokens}, "
                f"total: {total_tokens}"
            )

            if cached_tokens:
                print(f"[Cached Tokens: {cached_tokens}]")


async def log_chunk(
    category: Literal["content", "reasoning", "tool_call"],
    text: str,
) -> None:
    """Log streaming chunk with category marking.

    Args:
        category: Type of content (content, reasoning, tool_call)
        text: Chunk content
    """
    ts = get_timestamp()

    if category == "content":
        preview = text[:100] + "..." if len(text) > 100 else text
        print(f"[STREAM CHUNK] {ts} {preview}")

    elif category == "reasoning":
        preview = text[:100] + "..." if len(text) > 100 else text
        print(f"[STREAM CHUNK] {ts} [REASONING] {preview}")

    elif category == "tool_call":
        func_name = text
        print(f"[STREAM CHUNK] {ts} [TOOL_CALL] {func_name}")
