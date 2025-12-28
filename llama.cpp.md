# llama.cpp Integration Guide

## Overview

llama.cpp provides **full OpenAI-compatible API**, making it a drop-in replacement for cloud providers. The middleware can switch between zen (cloud) and llama.cpp (local) by changing a single configuration value.

---

## OpenAI-Compatible Endpoints

llama-server exposes all standard OpenAI endpoints:

| Endpoint | Description | Location |
|----------|-------------|-----------|
| `GET /v1/models` | List available models | server.cpp:171 |
| `POST /v1/chat/completions` | Chat completions | server.cpp:177 |
| `POST /v1/completions` | Text completions | server.cpp:175 |
| `POST /v1/embeddings` | Text embeddings | server.cpp:184 |

**No special flags required** - OpenAI compatibility is enabled by default.

---

## Request/Response Format

### Supported Request Parameters

| Parameter | Description | Source |
|-----------|-------------|---------|
| `model` | Model identifier | server-context.cpp:9894 |
| `messages` | Array of message objects | server-common.cpp:884 |
| `stream` | Enable SSE streaming | server-common.cpp:841 |
| `temperature` | Sampling temperature | Mapped from server params |
| `max_tokens` | Maximum tokens to generate | Mapped from server params |
| `top_p` | Nucleus sampling | Mapped from server params |
| `tools` | Tool definitions | server-common.cpp:839 |
| `tool_choice` | Tool selection mode | server-common.cpp:842 |
| `parallel_tool_calls` | Enable multiple tool calls | server-common.cpp:960 |

### Response Format

Standard OpenAI response:

```json
{
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello!",
      "tool_calls": [...]
    },
    "finish_reason": "stop"
  }],
  "created": 1234567890,
  "id": "chatcmpl-xxx",
  "model": "gpt-3.5-turbo",
  "object": "chat.completion",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 5,
    "total_tokens": 15
  }
}
```

**Implementation location**: `tools/server/server-task.cpp:613-707`

---

## Streaming Support

### SSE Format

llama.cpp emits standard Server-Sent Events:

**Format implementation**: `tools/server/server-common.cpp:1462`

```python
# SSE format
data: {"choices": [{"delta": {...}}]}

# Done marker
data: [DONE]
```

**Done marker location**: `tools/server/server-context.cpp:3005`

### Streaming Chunk Structure

Each chunk contains:

| Field | Description |
|--------|-------------|
| `choices[0].delta` | Incremental content update |
| `choices[0].finish_reason` | `null` until complete |
| `object` | Always `"chat.completion.chunk"` |
| `id` | Same across all chunks |
| `created` | Timestamp |

**Chunk generation**: `tools/server/server-task.cpp:728-796`

### Final Usage Chunk

When `include_usage` is true, an additional final chunk is sent:

```json
{
  "choices": [],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 5,
    "total_tokens": 15
  }
}
```

**Location**: `tools/server/server-task.cpp:768-783`

---

## Tool Calling

### Supported Parameters

| Parameter | Description |
|-----------|-------------|
| `tools` | Array of tool definitions |
| `tool_choice` | `"auto"`, `"required"`, or specific tool |
| `parallel_tool_calls` | Enable multiple tool calls simultaneously |

**Requires**: `--jinja` flag for native tool calling templates

### Native Tool Calling Models

Models with native function calling support:

- Llama 3.1 / 3.3 / 3.2
- Functionary v3.1 / v3.2
- Hermes 2/3
- Qwen 2.5 & Qwen 2.5 Coder
- Mistral Nemo
- Firefunction v2
- Command R7B
- DeepSeek R1

**Documentation**: `docs/function-calling.md:10-18`

### Generic Tool Calling

If model template is not recognized, generic tool call format is used.

**Documentation**: `docs/function-calling.md:20-22`

### Tool Call Response Format

```json
{
  "choices": [{
    "finish_reason": "tool_calls",
    "index": 0,
    "message": {
      "role": "assistant",
      "content": null,
      "tool_calls": [{
        "name": "python",
        "arguments": "{\"code\":\"...\"}"
      }]
    }
  }],
  "usage": {...}
}
```

**Implementation**: `tools/server/server-task.cpp:667`

### Example Tool Call Request

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "tools": [{
      "type": "function",
      "function": {
        "name": "python",
        "description": "Runs code in an ipython interpreter...",
        "parameters": {
          "type": "object",
          "properties": {
            "code": {"type": "string", "description": "Code to run"}
          },
          "required": ["code"]
        }
      }
    }],
    "messages": [{
      "role": "user",
      "content": "Print a hello world message with python."
    }]
  }'
```

**Documentation**: `docs/function-calling.md:335-362`

---

## Reasoning Content

**Status**: llama.cpp does NOT natively support a `reasoning_content` field in responses.

The `reasoning_content` field is **specific to GLM 4.7** and some reasoning models (e.g., DeepSeek R1).

### Middleware Handling

For middleware integration:

1. **GLM 4.7 (zen)**: Extract and log `reasoning_content` from `message.reasoning_content`
2. **llama.cpp**: Check if model is reasoning-capable (e.g., DeepSeek R1), handle accordingly
3. **Other models**: No `reasoning_content` field - ignore

### Reasoning Detection Logic

```python
def has_reasoning(message: Dict[str, Any]) -> bool:
    """
    Check if message contains reasoning content.

    GLM 4.7: message.reasoning_content
    DeepSeek R1: May have <think> tags in content
    Other: No reasoning
    """
    return "reasoning_content" in message
```

---

## Usage Statistics

llama.cpp provides standard usage statistics:

```json
{
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 10,
    "total_tokens": 60
  }
}
```

**Note**: No `cached_tokens` field like zen (GLM 4.7) has.

---

## Example Usage

### Using OpenAI Python SDK

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-no-key-required"
)

completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are ChatGPT..."},
        {"role": "user", "content": "Write a limerick..."}
    ]
)

print(completion.choices[0].message)
```

**Documentation**: `tools/server/README.md:1189-1206`

### Using curl

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer no-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "system", "content": "You are ChatGPT, an AI assistant."},
      {"role": "user", "content": "Write a limerick about python exceptions"}
    ]
  }'
```

**Documentation**: `tools/server/README.md:1211-1227`

### Embeddings

```bash
curl http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer no-key" \
  -d '{
    "input": "hello",
    "model": "GPT-4",
    "encoding_format": "float"
  }'
```

**Documentation**: `tools/server/README.md:1276-1284`

---

## Integration Points for Middleware

### 1. Base URL Configuration

Switch backends via `BACKEND_URL`:

**zen (cloud)**:
```bash
BACKEND_URL=https://opencode.ai/zen/v1
```

**llama.cpp (local)**:
```bash
BACKEND_URL=http://localhost:8080/v1
```

### 2. Authentication

**zen**: No API key for free models
**llama.cpp**: Use `"Bearer no-key"` or `"Bearer sk-no-key-required"`

### 3. Request Format

**Pass-through**: Both zen and llama.cpp accept standard OpenAI format

No transformation needed between client and backend.

### 4. Response Parsing

**Common fields**:
- `choices[0].message.content`
- `choices[0].message.tool_calls`
- `choices[0].finish_reason`
- `usage.prompt_tokens`
- `usage.completion_tokens`
- `usage.total_tokens`

**GLM 4.7 specific**:
- `choices[0].message.reasoning_content`
- `usage.prompt_tokens_details.cached_tokens`

### 5. Streaming

**Both use identical SSE format**:
- `data: {...}\n\n` for chunks
- `data: [DONE]\n\n` for completion

No parsing differences needed.

### 6. Model Discovery

**zen**:
- Fetch from `https://opencode.ai/zen/v1/models`
- Returns `{"object": "list", "data": [{"id": "...", ...}]}`

**llama.cpp**:
- Fetch from `http://localhost:8080/v1/models`
- Returns `[{"id": "...", ...}]` (array, not wrapped)

**Parsing difference**:
```python
async def fetch_models(base_url: str) -> list[str]:
    """Fetch models from backend."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/models")
        data = response.json()

        # zen: {"data": [...]}
        if isinstance(data, dict) and "data" in data:
            return [m["id"] for m in data["data"]]

        # llama.cpp: [...]
        return [m["id"] for m in data]
```

---

## Starting llama-server

### Basic Usage

```bash
# Start llama-server on port 8080
llama-server \
  --model path/to/model.gguf \
  --port 8080 \
  --host 0.0.0.0
```

### With Tool Calling

```bash
llama-server \
  --model qwen2.5-coder-7b-instruct.gguf \
  --jinja \  # Enable native tool calling
  --port 8080
```

### With All Optimizations

```bash
llama-server \
  --model qwen2.5-coder-32b-instruct.gguf \
  --jinja \
  --flash-attn on \
  --cont-batching \
  --parallel 8 \
  --n-gpu-layers -1 \
  --port 8080
```

---

## Testing

### Test Suite Locations

- `tools/server/tests/unit/test_chat_completion.py` - Chat completions
- `tools/server/tests/unit/test_tool_call.py` - Tool calling
- `tools/server/tests/unit/test_infill.py` - Fill-in-the-middle

### Manual Testing

```bash
# Test chat completions
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}'

# Test models endpoint
curl http://localhost:8080/v1/models

# Test health
curl http://localhost:8080/health
```

---

## Key Files

| File | Purpose |
|------|---------|
| `tools/server/README.md` | Server documentation and examples |
| `tools/server/server.cpp` | Main server implementation |
| `tools/server/server-common.cpp` | Request parsing and shared logic |
| `tools/server/server-task.cpp` | Response generation |
| `tools/server/server-context.cpp` | Context management |
| `docs/function-calling.md` | Tool calling documentation |

---

## Advantages for Middleware

1. **Drop-in replacement**: Same API as OpenAI/zen
2. **No code changes**: Switch via `BACKEND_URL` configuration
3. **Full feature parity**: Chat, tools, streaming, embeddings
4. **Local privacy**: No data leaves your machine
5. **Cost control**: No per-token API costs
6. **Model flexibility**: Run any GGUF model

---

## Limitations

1. **No `reasoning_content` field**: This is GLM 4.7 specific
2. **No `cached_tokens`**: llama.cpp doesn't track cache hits
3. **Hardware requirements**: Needs sufficient RAM/VRAM for model size
4. **Model file management**: Must download GGUF files manually

---

## Future Enhancements

1. **Model auto-detection**: Scan local directory for GGUF files
2. **State management**: Integrate KV cache save/load
3. **Multi-model routing**: Route different requests to different models
4. **Speculative decoding**: Use draft models for faster generation
5. **Grammar constraints**: Enforce JSON/tool call formats via GBNF
