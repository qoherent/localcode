"""
LocalCode Middleware Server
Sits between OpenCode and GLM 4.7 API, logging all requests/responses.
"""

import asyncio
import json
import httpx
import uvicorn
from typing import Any, AsyncGenerator, Dict, List, Union
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import time


GLM_API_URL = "https://api.z.ai/api/coding/paas/v4"
PORT = 4242
API_KEY = "dummy"

app = FastAPI()


def log_request(request_data: Dict[str, Any]) -> None:
    """Pretty print incoming request from OpenCode."""
    print(f"\n{'=' * 80}")
    print(f"[REQUEST] {time.strftime('%H:%M:%S')}")
    print(f"Model: {request_data.get('model', 'unknown')}")

    if "stream" in request_data:
        print(f"Stream: {request_data['stream']}")

    messages = request_data.get("messages", [])
    if messages:
        print(f"Messages count: {len(messages)}")
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            content_type = type(content).__name__

            if role == "tool" and "tool_call_id" in msg:
                print(f"  [{i}] Tool Result: {msg.get('tool_call_id', 'no-id')}")
                print(f"      Type: {content_type}")
            elif role == "assistant" and isinstance(content, list):
                tool_calls = [
                    p
                    for p in content
                    if isinstance(p, dict) and p.get("type") == "tool-call"
                ]
                text_parts = [
                    p
                    for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]

                print(f"  [{i}] Assistant:")
                if text_parts:
                    text = "".join(p.get("text", "") for p in text_parts)
                    preview = text[:100] + "..." if len(text) > 100 else text
                    print(f"      Text: {preview}")

                if tool_calls:
                    for tc in tool_calls:
                        func_name = tc.get("function", {}).get("name", "unknown")
                        print(f"      [Tool Call] {func_name}")
                        func_args = tc.get("function", {}).get("arguments", "{}")
                        args_preview = (
                            func_args[:200] if len(func_args) > 200 else func_args
                        )
                        print(f"      Args: {args_preview}")
            else:
                if isinstance(content, list):
                    preview = str(content)[:150]
                elif isinstance(content, str):
                    preview = content[:100] + "..." if len(content) > 100 else content
                else:
                    preview = str(content)[:100]
                print(f"  [{i}] {role}: {preview}")

    if "tools" in request_data:
        tools = request_data["tools"]
        print(f"[Tool Definitions] {len(tools)} tools")
        for i, tool in enumerate(tools):
            name = tool.get("function", {}).get("name", "unknown")
            desc = tool.get("function", {}).get("description", "no description")[:60]
            print(f"  [{i}] {name}: {desc}")

    print(f"{'=' * 80}\n")


def log_response(response_data: Dict[str, Any]) -> None:
    """Pretty print response from GLM 4.7."""
    print(f"\n{'-' * 80}")
    print(f"[RESPONSE] {time.strftime('%H:%M:%S')}")

    choices = response_data.get("choices", [])
    if choices:
        choice = choices[0]
        msg = choice.get("message", {})

        content = msg.get("content")
        if content:
            preview = content[:150] + "..." if len(content) > 150 else content
            print(f"Content: {preview}")

        tool_calls = msg.get("tool_calls", [])
        if tool_calls:
            for tc in tool_calls:
                func_name = tc.get("function", {}).get("name", "unknown")
                print(f"[Tool Call] {func_name}")
                func_args = tc.get("function", {}).get("arguments", "{}")
                args_preview = func_args[:200] if len(func_args) > 200 else func_args
                print(f"Args: {args_preview}")

        finish_reason = choice.get("finish_reason", "unknown")
        print(f"Finish reason: {finish_reason}")

    usage = response_data.get("usage", {})
    if usage:
        print(
            f"Usage - prompt: {usage.get('prompt_tokens', 0)}, "
            f"completion: {usage.get('completion_tokens', 0)}, "
            f"total: {usage.get('total_tokens', 0)}"
        )

    print(f"{'-' * 80}\n")


def log_stream_chunk(chunk: str) -> None:
    """Log streaming chunks."""
    print(
        f"[STREAM CHUNK] {time.strftime('%H:%M:%S')} {chunk[:100] if len(chunk) > 100 else chunk}"
    )


def has_tool_calls(request_data: Dict[str, Any]) -> bool:
    """Check if request contains tool definitions."""
    tools = request_data.get("tools", [])
    return len(tools) > 0


def transform_request_to_glm(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform OpenCode request to GLM 4.7 format."""
    glm_request = {
        "model": request_data.get("model", "glm-4.7"),
        "messages": request_data.get("messages", []),
    }

    if "stream" in request_data:
        glm_request["stream"] = request_data["stream"]

    if "temperature" in request_data:
        glm_request["temperature"] = request_data["temperature"]

    if "max_tokens" in request_data:
        glm_request["max_tokens"] = request_data["max_tokens"]

    if "top_p" in request_data:
        glm_request["top_p"] = request_data["top_p"]

    if has_tool_calls(request_data):
        print(f"[Tool Request] Detected tools in request")
        glm_request["tools"] = request_data["tools"]

    return glm_request


async def forward_request(
    glm_request: Dict[str, Any], stream: bool = False
) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
    """Forward request to GLM 4.7 API."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        if stream:
            async with client.stream(
                "POST",
                f"{GLM_API_URL}/chat/completions",
                headers=headers,
                json=glm_request,
            ) as response:
                response.raise_for_status()

                async for chunk in response.aiter_bytes():
                    chunk_str = chunk.decode("utf-8")

                    lines = [line for line in chunk_str.split("\n") if line.strip()]

                    for line in lines:
                        if line.startswith("data: "):
                            data_str = line[6:].strip()

                            if data_str == "[DONE]":
                                yield {"type": "done"}
                                return

                            try:
                                data = json.loads(data_str)
                                yield {"type": "chunk", "data": data}
                            except json.JSONDecodeError:
                                pass
        else:
            response = await client.post(
                f"{GLM_API_URL}/chat/completions", headers=headers, json=glm_request
            )
            response.raise_for_status()
            yield {"type": "complete", "data": response.json()}


async def stream_generator(
    forward_gen: AsyncGenerator[Union[str, Dict[str, Any]], None], is_tool_request: bool
) -> AsyncGenerator[str, None]:
    """Generate SSE stream for streaming responses."""
    try:
        async for item in forward_gen:
            item_type = item.get("type")

            if item_type == "chunk":
                data = item.get("data", {})
                choices = data.get("choices", [])

                if choices:
                    choice = choices[0]
                    delta = choice.get("delta", {})

                    if "content" in delta:
                        content = delta["content"]
                        log_stream_chunk(content)
                        yield f"data: {json.dumps(data)}\n\n"

                    if "tool_calls" in delta:
                        print(f"[Tool Call Stream] Detected tool call in delta")
                        yield f"data: {json.dumps(data)}\n\n"

                    finish_reason = choice.get("finish_reason")
                    if finish_reason:
                        if finish_reason == "tool_calls":
                            print(f"[Tool Call Complete] Finish reason: tool_calls")
                        yield f"data: {json.dumps(data)}\n\n"

            elif item_type == "done":
                yield "data: [DONE]\n\n"
                return

            elif item_type == "complete":
                data = item.get("data", {})
                log_response(data)
                yield f"data: {json.dumps(data)}\n\n"
                yield "data: [DONE]\n\n"
                return

    except Exception as e:
        print(f"[ERROR] Streaming error: {e}")
        yield f"data: {json.dumps({'error': {'message': str(e)}})}\n\n"
        yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Handle OpenAI-compatible chat completions."""
    request_data = await request.json()

    log_request(request_data)

    is_stream = request_data.get("stream", False)
    is_tool_request = has_tool_calls(request_data)

    glm_request = transform_request_to_glm(request_data)

    forward_gen = forward_request(glm_request, stream=is_stream)

    if is_stream:
        return StreamingResponse(
            stream_generator(forward_gen, is_tool_request),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    else:
        result = None
        async for item in forward_gen:
            if item.get("type") == "complete":
                result = item.get("data")
                break

        if result:
            log_response(result)
            return result

        return {"error": {"message": "No response from upstream"}}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "provider": "LocalCode", "model": "GLM-4.7"}


def main():
    """Run the server."""
    print(f"\n{'#' * 80}")
    print(f"# LocalCode Middleware Server")
    print(f"# Listening on http://0.0.0.0:{PORT}")
    print(f"# Forwarding to GLM 4.7: {GLM_API_URL}")
    print(f"{'#' * 80}\n")

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")


if __name__ == "__main__":
    main()
