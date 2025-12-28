"""Generic OpenAI-compatible HTTP client."""

import json
import httpx
from typing import Any, AsyncGenerator, Dict


async def fetch_models(base_url: str) -> list[str]:
    """Fetch available models from backend /v1/models endpoint.

    Args:
        base_url: Backend base URL (e.g., https://opencode.ai/zen/v1)

    Returns:
        List of model IDs

    Note:
        - zen: Returns {"object": "list", "data": [{"id": "...", ...}]}
        - llama.cpp: Returns [{"id": "...", ...}]
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{base_url}/models")
        response.raise_for_status()

        data = response.json()

        # zen: {"data": [...]}
        if isinstance(data, dict) and "data" in data:
            return [m["id"] for m in data["data"]]

        # llama.cpp: [...]
        if isinstance(data, list):
            return [m["id"] for m in data]

        # Unknown format, try to extract ids
        if isinstance(data, list):
            return [str(m) for m in data]

        return []


async def post_chat_completions(
    request: Dict[str, Any],
    backend_url: str,
    api_key: str = "",
) -> AsyncGenerator[Dict[str, Any], None]:
    """POST to /v1/chat/completions.

    Args:
        request: Request data (model, messages, stream, tools, etc.)
        backend_url: Backend base URL
        api_key: API key (empty string for free models)

    Yields:
        Events as dictionaries:
        - {"type": "chunk", "data": {...}} - Streaming chunk
        - {"type": "complete", "data": {...}} - Full response (non-stream)
        - {"type": "done"} - Stream complete marker
        - {"type": "error", "message": "..."} - Error occurred

    Note:
        Works with any OpenAI-compatible backend (zen, llama.cpp, etc.)
    """
    headers = {
        "Content-Type": "application/json",
    }

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    is_stream = request.get("stream", False)

    async with httpx.AsyncClient(timeout=300.0) as client:
        if is_stream:
            async with client.stream(
                "POST",
                f"{backend_url}/chat/completions",
                headers=headers,
                json=request,
            ) as response:
                response.raise_for_status()

                async for chunk_data in parse_sse_chunks(response):
                    yield chunk_data
        else:
            response = await client.post(
                f"{backend_url}/chat/completions",
                headers=headers,
                json=request,
            )
            response.raise_for_status()
            yield {"type": "complete", "data": response.json()}


async def parse_sse_chunks(
    response: httpx.Response,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Parse SSE stream into discrete events.

    Args:
        response: HTTPX streaming response

    Yields:
        Events as dictionaries:
        - {"type": "chunk", "data": {...}} - Parsed JSON chunk
        - {"type": "done"} - [DONE] marker
        - {"type": "error", "message": "..."} - Parse error

    SSE Format:
        data: {"choices": [...]}
        data: {"choices": [...]}
        data: [DONE]
    """
    buffer = ""

    async for chunk in response.aiter_bytes():
        chunk_str = chunk.decode("utf-8")
        buffer += chunk_str

        lines = buffer.split("\n")
        buffer = lines.pop() if lines else ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("data: "):
                data_str = line[6:].strip()

                if data_str == "[DONE]":
                    yield {"type": "done"}
                    return

                try:
                    data = json.loads(data_str)
                    yield {"type": "chunk", "data": data}
                except json.JSONDecodeError:
                    yield {
                        "type": "error",
                        "message": f"Failed to parse JSON: {data_str}",
                    }


async def select_free_model(backend_url: str) -> str:
    """Fetch models and select first free model for zen backend.

    Args:
        backend_url: Backend base URL

    Returns:
        First free model ID

    Note:
        - For zen: Returns first known free model (glm-4.7-free, etc.)
        - For llama.cpp: Returns first available model
    """
    models = await fetch_models(backend_url)

    if not models:
        raise RuntimeError("No models available from backend")

    # For zen, prioritize known free models
    if "opencode.ai" in backend_url:
        known_free = [
            "glm-4.7-free",
            "big-pickle",
            "grok-code",
            "alpha-gd4",
        ]

        for model_id in known_free:
            if model_id in models:
                return model_id

    # Fallback to first available model
    return models[0]
