"""Request/response processing functions."""

from typing import Any, Dict, Optional, Tuple


def extract_request_info(request: Dict[str, Any]) -> Dict[str, Any]:
    """Extract structured info from OpenCode request.

    Args:
        request: Request data from OpenCode

    Returns:
        Dictionary with keys:
            - model: Model identifier
            - stream: Whether streaming is enabled
            - messages_count: Number of messages
            - has_tools: Whether tools are defined
            - tools_count: Number of tools (if any)
    """
    model = request.get("model", "unknown")
    is_stream = request.get("stream", False)

    messages = request.get("messages", [])
    messages_count = len(messages)

    tools = request.get("tools", [])
    has_tools = len(tools) > 0
    tools_count = len(tools) if has_tools else 0

    return {
        "model": model,
        "stream": is_stream,
        "messages_count": messages_count,
        "has_tools": has_tools,
        "tools_count": tools_count,
    }


def extract_message_parts(
    message_or_delta: Dict[str, Any],
) -> Tuple[Optional[str], Optional[str], Optional[list]]:
    """Extract content, reasoning, and tool_calls from message.

    Args:
        message_or_delta: Message or delta from backend

    Returns:
        Tuple of (content, reasoning_content, tool_calls)

    Examples:
        # Regular message
        ("Hello", None, None)

        # With reasoning (GLM 4.7)
        ("4", "1+1=2, so 2+2=4", None)

        # Tool call
        (None, None, [{...tool_call...}])
    """
    content = message_or_delta.get("content")
    reasoning_content = message_or_delta.get("reasoning_content")
    tool_calls = message_or_delta.get("tool_calls")

    return content, reasoning_content, tool_calls


def extract_usage_stats(response: Dict[str, Any]) -> Dict[str, Any]:
    """Extract token usage with cache info.

    Args:
        response: Full response from backend

    Returns:
        Dictionary with keys:
            - prompt_tokens: Number of prompt tokens
            - completion_tokens: Number of completion tokens
            - total_tokens: Total tokens used
            - cached_tokens: Cached tokens (optional, None if not present)
    """
    usage = response.get("usage", {})

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)

    cached_tokens = None
    if "prompt_tokens_details" in usage:
        cached_tokens = usage["prompt_tokens_details"].get("cached_tokens")

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cached_tokens": cached_tokens,
    }


def categorize_delta(
    delta: Dict[str, Any],
) -> str:
    """Categorize streaming delta content.

    Args:
        delta: Delta object from backend

    Returns:
        Category: "content", "reasoning", "tool_call", or "none"

    Priority:
        1. tool_calls → "tool_call"
        2. reasoning_content → "reasoning"
        3. content → "content"
        4. else → "none"
    """
    if "tool_calls" in delta:
        return "tool_call"

    if "reasoning_content" in delta:
        return "reasoning"

    if "content" in delta:
        return "content"

    return "none"


def get_finish_reason(response: Dict[str, Any]) -> str:
    """Extract finish reason from response.

    Args:
        response: Response from backend

    Returns:
        Finish reason (stop, tool_calls, etc.)
    """
    choices = response.get("choices", [])
    if choices:
        return choices[0].get("finish_reason", "unknown")

    return "unknown"
