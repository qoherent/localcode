# LocalCode Middleware Server

A Python middleware server that sits between OpenCode and GLM 4.7, logging all requests and responses.

## Features

- **OpenAI-Compatible API**: `/v1/chat/completions` endpoint
- **Request Logging**: Pretty prints all incoming requests
- **Response Logging**: Pretty prints all outgoing responses
- **Streaming Support**: Native Python async generators
- **Tool Call Markers**: Detects and marks tool requests in logs
- **Functional Design**: No OOP, pure functions

## Installation

```bash
cd LocalCode
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

Server starts on `http://0.0.0.0:4242`

## OpenCode Configuration

Add to OpenCode provider configuration:

```typescript
{
  "localcode": {
    "npm": "@ai-sdk/openai-compatible",
    "api": "http://localhost:4242/v1",
    "name": "LocalCode",
    "models": {
      "glm-4.7": {
        "id": "glm-4.7",
        "name": "GLM-4.7 (via LocalCode)",
        "family": "glm-4.7",
        "reasoning": true,
        "tool_call": true,
        "temperature": true,
        "cost": {
          "input": 0,
          "output": 0
        },
        "limit": {
          "context": 204800,
          "output": 131072
        }
      }
    }
  }
}
```

Or configure via environment:

```bash
export OPENCODE_PROVIDER_URL="http://localhost:4242/v1"
```

## API Endpoints

### POST /v1/chat/completions

OpenAI-compatible chat completions endpoint.

**Request Format:**

```json
{
  "model": "glm-4.7",
  "messages": [{ "role": "user", "content": "Hello" }],
  "stream": false,
  "temperature": 0.8,
  "max_tokens": 2000
}
```

**Response Format:**

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

**Tool Call Example:**

```json
{
  "model": "glm-4.7",
  "messages": [{ "role": "user", "content": "Edit file" }],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "edit",
        "parameters": {
          "type": "object",
          "properties": {
            "filePath": { "type": "string" },
            "oldString": { "type": "string" },
            "newString": { "type": "string" }
          }
        }
      }
    }
  ]
}
```

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

## Log Output

The middleware prints detailed logs to console:

### Request Log

```
================================================================================
[REQUEST] 14:32:15
Model: glm-4.7
Stream: false
Messages count: 2
  [0] system: You are a coding agent...
  [1] user: Edit the function...
[Tool Definitions] 3 tools
  [0] edit: Edits a file...
================================================================================
```

### Response Log

```
--------------------------------------------------------------------------------
[RESPONSE] 14:32:20
Content: Sure, I'll help you edit the function...
Finish reason: stop
Usage - prompt: 150, completion: 45, total: 195
--------------------------------------------------------------------------------
```

### Tool Call Markers

```
[Tool Request] Detected tools in request
[Tool Call] edit
Args: {"filePath": "/src/app.ts", "oldString": "...", "newString": "..."}
```

### Stream Chunks

```
[STREAM CHUNK] 14:32:18 Sure
[STREAM CHUNK] 14:32:18 , I'll
[STREAM CHUNK] 14:32:18  help
```

## Configuration

Constants in `main.py`:

```python
GLM_API_URL = "https://api.z.ai/api/coding/paas/v4"
PORT = 4242
API_KEY = "dummy"  # GLM 4.7 is free
```

## Development

### Running with custom port:

```python
# Edit main.py
PORT = 8080
```

### Verbose logging:

Logs are always printed to stdout. Redirect to file:

```bash
python main.py 2>&1 | tee middleware.log
```

## Troubleshooting

### Port already in use:

```bash
lsof -ti:4242 | xargs kill -9
```

### Import errors:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## License

Same as parent OpenCode project.
