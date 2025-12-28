"""FastAPI server with OpenAI-compatible endpoints."""

import json
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse


def create_app(
    backend_url: str,
    log_event: Callable,
    post_chat_completions: Callable,
    processor: dict,
) -> FastAPI:
    """Create FastAPI app with all dependencies injected.

    Args:
        backend_url: Backend API URL
        log_event: Logging function
        post_chat_completions: Client function for chat completions
        processor: Dict of processor functions

    Returns:
        Configured FastAPI application
    """

    app = FastAPI()

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        """Handle OpenAI-compatible chat completions."""
        request_data = await request.json()

        request_info = processor["extract_request_info"](request_data)
        await log_event("request_start", request_info)

        is_stream = request_data.get("stream", False)

        if is_stream:
            return StreamingResponse(
                stream_generator(
                    request_data,
                    backend_url,
                    log_event,
                    post_chat_completions,
                    processor,
                ),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        else:
            result = None
            async for event in post_chat_completions(request_data, backend_url):
                if event.get("type") == "complete":
                    result = event.get("data")
                    break

            if result:
                content, reasoning, tool_calls = processor["extract_message_parts"](
                    result.get("choices", [{}])[0].get("message", {})
                )
                usage = processor["extract_usage_stats"](result)
                finish_reason = processor["get_finish_reason"](result)

                await log_event(
                    "response_end",
                    {
                        "content": content,
                        "reasoning": reasoning,
                        "tool_calls": tool_calls,
                        "finish_reason": finish_reason,
                        "usage": usage,
                    },
                )
                return result

            return {"error": {"message": "No response from upstream"}}

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "ok",
            "provider": "LocalCode Middleware",
            "backend_url": backend_url,
        }

    return app


async def stream_generator(
    request_data: dict,
    backend_url: str,
    log_event: Callable,
    post_chat_completions: Callable,
    processor: dict,
):
    """Generate SSE stream for streaming responses.

    Args:
        request_data: Original request from OpenCode
        backend_url: Backend API URL
        log_event: Logging function
        post_chat_completions: Client function
        processor: Dict of processor functions

    Yields:
        SSE-formatted strings (data: {...}\n\n or data: [DONE]\n\n)
    """
    async for event in post_chat_completions(request_data, backend_url):
        event_type = event.get("type")

        if event_type == "chunk":
            data = event.get("data", {})
            choices = data.get("choices", [])

            if choices:
                choice = choices[0]
                delta = choice.get("delta", {})

                category = processor["categorize_delta"](delta)

                if category == "content":
                    content = delta.get("content", "")
                    if content:
                        await log_event(
                            "stream_chunk", {"category": "content", "content": content}
                        )

                elif category == "reasoning":
                    reasoning = delta.get("reasoning_content", "")
                    if reasoning:
                        await log_event(
                            "stream_chunk",
                            {"category": "reasoning", "content": reasoning},
                        )

                elif category == "tool_call":
                    tool_calls = delta.get("tool_calls", [])
                    for tc in tool_calls:
                        func_name = tc.get("function", {}).get("name", "unknown")
                        await log_event("tool_call", {"function_name": func_name})

                yield f"data: {json.dumps(data)}\n\n"

        elif event_type == "done":
            await log_event("response_end", {"timestamp": "done"})
            yield "data: [DONE]\n\n"
            return

        elif event_type == "error":
            message = event.get("message", "Unknown error")
            await log_event("error", {"message": message})
            yield f"data: {json.dumps({'error': {'message': message}})}\n\n"
            yield "data: [DONE]\n\n"
            return
