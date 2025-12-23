# LocalCode Middleware Architecture

## Overview

LocalCode is a Python middleware server that sits between OpenCode (client) and various LLM backends (currently GLM 4.7). It provides request interception, intelligent caching, and request transformation to optimize local LLM execution speed.

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  OpenCode   │────▶│  LocalCode   │────▶│   Backend    │
│   Client    │     │  Middleware  │     │  (GLM 4.7) │
└─────────────┘     └──────────────┘     └──────────────┘
```

## End Goals

### Phase 1: Request Interception & Logging ✅

- [x] OpenAI-compatible API (`/v1/chat/completions`)
- [x] Request/response logging with pretty printing
- [x] Streaming support (native async generators)
- [x] Tool call detection and markers
- [x] Health check endpoint

### Phase 2: State Management (Planned)

- [ ] KV cache hashing based on system prompt + message history
- [ ] State save/load to disk (bypass prefill latency)
- [ ] LRU cache for session states
- [ ] Cache key computation: `SHA256(system_prompt + messages + tools)`

### Phase 3: llama.cpp Integration (Planned)

- [ ] Speculative decoding orchestration (draft/target model pairs)
- [ ] KV cache state management (slot hot-swap)
- [ ] Continuous batching for multi-user throughput
- [ ] Flash attention optimization
- [ ] Grammar constraint enforcement (GBNF)
- [ ] Native function calling support
- [ ] FIM (Fill-In-The-Middle) completions
- [ ] Control vector runtime steering
- [ ] Multimodal support (vision projectors)
- [ ] Reranking for codebase search

### Phase 4: Intelligent Routing (Planned)

- [ ] Multi-model routing (coder vs. general vs. vision)
- [ ] Request type classification
- [ ] Dynamic model selection based on request content
- [ ] Adaptive caching strategies

## Current Implementation Status

### ✅ Completed Features

**Core Server** (`main.py`)

- FastAPI server listening on port 4242
- OpenAI-compatible `/v1/chat/completions` endpoint
- `/health` health check endpoint

**Request Logging**

- `log_request()` - Pretty prints incoming requests
- Model, stream status, messages count
- Tool definitions logging
- Message role detection (system, user, assistant, tool)
- Content previewing (truncated at 100-150 chars)

**Response Logging**

- `log_response()` - Pretty prints GLM responses
- Content preview, tool calls, finish reason
- Token usage tracking (prompt, completion, total)

**Tool Detection**

- `has_tool_calls()` - Detects tools in request
- `transform_request_to_glm()` - Passes through tool definitions
- Tool call markers: `[Tool Request]`, `[Tool Call]`, `[Tool Call Complete]`

**Streaming**

- `stream_generator()` - Native Python async generators
- SSE (Server-Sent Events) format
- `data:` prefix and `[DONE]` marker handling
- Chunk-by-chunk logging

**Functional Design**

- Pure functions (no OOP)
- Type hints with `Dict[str, Any]`, `AsyncGenerator`
- Separated concerns: logging, transformation, forwarding

### 🚧 In Progress

None - focusing on Phase 1 completion.

### 📋 Next Steps

**Phase 2: State Management**

1. Add SHA256 hashing function for cache keys
2. Implement cache directory structure
3. Add `save_state()` and `load_state()` functions
4. Implement LRU eviction policy

**Phase 3: llama.cpp Integration**

1. Add llama.cpp backend support alongside GLM 4.7
2. Implement slot management API
3. Add grammar constraint enforcement
4. Implement speculative decoding orchestration

## Architecture Decisions

### Functional Programming over OOP

- Pure functions instead of classes
- Explicit data flow (no hidden state)
- Testable in isolation
- Easier to reason about

### Async/Await Pattern

- Native Python async generators for streaming
- Non-blocking I/O for multiple concurrent requests
- `AsyncGenerator[str, None]` for SSE streams

### OpenAI-Compatible API

- Standard OpenAI request/response format
- Allows drop-in replacement for existing providers
- Tool calling support via OpenAI format
- Streaming via SSE

### Configuration

Constants in `main.py`:

```python
GLM_API_URL = "https://api.z.ai/api/coding/paas/v4"
PORT = 4242
API_KEY = "dummy"
```

## File Structure

```
LocalCode/
├── main.py              # Main FastAPI server
├── pyproject.toml       # Poetry configuration
├── poetry.lock          # Dependency lockfile
└── ARCHITECTURE.md      # This file
```

## API Endpoints

### POST /v1/chat/completions

OpenAI-compatible chat completions endpoint.

**Supported Parameters:**

- `model` - Model identifier (default: "glm-4.7")
- `messages` - Array of message objects
- `stream` - Enable streaming (default: false)
- `temperature` - Sampling temperature
- `max_tokens` - Maximum tokens to generate
- `top_p` - Nucleus sampling parameter
- `tools` - Array of tool definitions (passed through)

**Response Format:**

- Non-streaming: Full JSON response
- Streaming: SSE stream with `data:` prefix

### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "ok",
  "provider": "LocalCode",
  "model": "GLM-4.7"
}
```

## Dependencies

**Core:**

- `fastapi` - Web framework
- `httpx` - Async HTTP client
- `uvicorn[standard]` - ASGI server

**Development:**

- `pytest` - Testing framework
- `pytest-asyncio` - Async test support

## Future Roadmap

### Short Term (Phase 2)

- KV cache state persistence
- Session state hot-swapping
- Request hash-based caching

### Medium Term (Phase 3)

- llama.cpp backend integration
- Speculative decoding
- Grammar constraints
- Native function calling

### Long Term (Phase 4)

- Multi-model intelligent routing
- Control vector runtime steering
- Multimodal support
- Reranking optimization

## Related Documentation

- `middleware.md` - llama.cpp & OpenCode advanced integration research
- `README.md` - Installation and usage guide
- `pyproject.toml` - Package configuration
