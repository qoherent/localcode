# LocalCode Middleware Server

A modular Python middleware server that sits between OpenCode and OpenAI-compatible backends (zen, llama.cpp, etc.), with structured logging and extensible architecture.

## Features

- **Modular Architecture**: Separated into functional modules (config, client, logger, processor, server)
- **Backend Agnostic**: Works with any OpenAI-compatible API (zen, llama.cpp, etc.)
- **Structured Logging**: Clean, labeled event logging for debugging and analysis
- **Reasoning Content Support**: Detects and marks reasoning content from GLM 4.7
- **Tool Call Detection**: Identifies and logs tool requests and responses
- **Streaming Support**: Native Python async generators for SSE streaming
- **Configuration via .env**: Simple environment variable configuration
- **Functional Design**: Pure functions, no OOP, easy to test

## Installation

```bash
cd localcode
poetry install
```

## Configuration

The middleware reads configuration from a `.env` file in the project root.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `4242` | Server listening port |
| `BACKEND_URL` | `https://opencode.ai/zen/v1` | Backend API URL |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARN, ERROR) |

### Setting Up Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` to configure your backend:
   
   **For cloud (zen):**
   ```bash
   PORT=4242
   BACKEND_URL=https://opencode.ai/zen/v1
   LOG_LEVEL=INFO
   ```
   
   **For local (llama.cpp):**
   ```bash
   PORT=4242
   BACKEND_URL=http://localhost:8080/v1
   LOG_LEVEL=INFO
   ```

3. Start the server:
   ```bash
   poetry run python main.py
   ```

### Switching Backends

To switch from cloud to local (or vice versa), simply edit `BACKEND_URL` in `.env` and restart the server.

## Running

```bash
# Start with default configuration
poetry run python main.py

# Server will auto-detect free model for zen backend
# and print startup banner like:

################################################################################
# LocalCode Middleware Server
# Listening on http://0.0.0.0:4242
# Backend: https://opencode.ai/zen/v1
# Selected Model: glm-4.7-free (auto-detected)
################################################################################
```

## API Endpoints

### POST /v1/chat/completions

OpenAI-compatible chat completions endpoint.

**Request Format:**

```json
{
  "model": "glm-4.7-free",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "stream": false,
  "temperature": 0.8,
  "max_tokens": 2000
}
```

**With Tools:**

```json
{
  "model": "glm-4.7-free",
  "messages": [
    {"role": "user", "content": "Edit file"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "edit",
        "parameters": {
          "type": "object",
          "properties": {
            "filePath": {"type": "string"},
            "oldString": {"type": "string"},
            "newString": {"type": "string"}
          }
        }
      }
    }
  ]
}
```

**Response Format (Non-Streaming):**

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "glm-4.7",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello!"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 5,
    "total_tokens": 15
  }
}
```

**With Reasoning (GLM 4.7):**

```json
{
  "choices": [
    {
      "message": {
        "content": "4",
        "reasoning_content": "1+1=2, so 2+2=4"
      },
      "finish_reason": "stop"
    }
  ]
}
```

**Streaming Response:**

Standard SSE (Server-Sent Events) format:

```
data: {"choices":[{"delta":{"content":"Hello"}}]}

data: {"choices":[{"delta":{"content":" world!"}}]}

data: [DONE]
```

### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "ok",
  "provider": "LocalCode Middleware",
  "backend_url": "https://opencode.ai/zen/v1"
}
```

## Log Output

The middleware prints structured logs to console:

### Request Log

```
================================================================================
[REQUEST] 12:34:56
Model: glm-4.7-free
Stream: False
Messages count: 1
[Tool Definitions] 2 tools
  [0] edit: Edits a file...
  [1] read: Reads file...
================================================================================
```

### Response Log

```
--------------------------------------------------------------------------------
[RESPONSE] 12:34:58
Content: I'll help you edit the function...
Finish reason: stop
Usage - prompt: 150, completion: 45, total: 195
[Cached Tokens: 12]
--------------------------------------------------------------------------------
```

### Tool Call Log

```
[Tool Call] edit
Args: {"filePath": "/src/app.ts", "oldString": "...", "newString": "..."}
```

### Reasoning Log

```
[STREAM CHUNK] 12:34:57 [REASONING] The user asked for 2+2...
[STREAM CHUNK] 12:34:58 [REASONING] 2+2 = 4...
[STREAM CHUNK] 12:34:59 4
```

### Stream Chunk Log

```
[STREAM CHUNK] 12:34:58 Hello
[STREAM CHUNK] 12:34:58  world!
```

## Development

### Running Tests

```bash
# Run all tests
poetry run python config.test.py -v
poetry run python logger.test.py -v
poetry run python processor.test.py -v
poetry run python client.test.py -v
poetry run python server.test.py -v
```

### Project Structure

```
localcode/
├── .env.example          # Configuration template
├── .env                 # Your configuration (created by you)
├── config.py             # Configuration loading
├── config.test.py         # Configuration tests
├── logger.py             # Structured event logging
├── logger.test.py         # Logger tests
├── client.py             # OpenAI-compatible HTTP client
├── client.test.py         # Client tests
├── processor.py           # Request/response processing
├── processor.test.py       # Processor tests
├── server.py             # FastAPI application
├── server.test.py         # Server tests
├── main.py               # Entry point
├── README.md             # This file
├── pyproject.toml        # Poetry dependencies
├── llama.cpp.md          # llama.cpp integration guide
├── ARCHITECTURE.md       # Architecture documentation
└── middleware.md         # Middleware research
```

## Troubleshooting

### Port already in use:

```bash
# Find and kill process using port 4242
lsof -ti:4242 | xargs kill -9
```

### Dependencies not found:

```bash
poetry install
```

### Backend connection errors:

1. Check `BACKEND_URL` in `.env`
2. For zen: Ensure you have internet access
3. For llama.cpp: Ensure llama-server is running on the specified URL

## Architecture

See `ARCHITECTURE.md` for detailed design documentation and future roadmap.

## License

Same as parent OpenCode project.
