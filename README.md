# LocalCode Middleware Server

A lightweight OpenAI-compatible proxy for OpenCode that routes requests to OpenCode Zen (free GLM 4.7) or local llama.cpp. Powered by [LiteLLM](https://litellm.ai/).

## Features

- **OpenAI-Compatible API**: `/v1/chat/completions` endpoint
- **Free Models**: GLM 4.7, Big Pickle, Grok Code, Alpha GD4 via OpenCode Zen
- **Local Models**: llama.cpp via local server
- **Auto-Retries**: Built-in retry logic for rate limits (429)
- **Connection Pooling**: Efficient httpx client reuse
- **Structured Logging**: Request/response/event logging with category markers

## Installation

```bash
# Install with poetry
cd localcode
poetry install

# Or with pip
pip install litellm pyyaml
```

## Configuration

Edit `config.yaml` to configure models and settings:

```yaml
model_list:
  - model_name: glm-4.7-free
    litellm_params:
      model: glm-4.7-free
      api_base: https://opencode.ai/zen/v1
      api_key: "public"  # Free tier - no key needed
      max_retries: 3
      retry_after: 10  # Wait 10s on 429 before retry
      timeout: 300.0

litellm_settings:
  default_max_retries: 3
  default_retry_after: 10
  allow_auth_on_null_key: true
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LITELLM_CONFIG` | `config.yaml` | Path to config file |
| `LITELLM_HOST` | `0.0.0.0` | Server host |
| `LITELLM_PORT` | `4242` | Server port |
| `LITELLM_LOGLEVEL` | `INFO` | Logging level |

## Running

```bash
# Start with default config
poetry run python main.py

# Or use litellm directly
litellm --config config.yaml

# Custom port
poetry run python main.py --port 8080

# Custom config
poetry run python main.py --config my-config.yaml
```

## Switching Backends

### Cloud (OpenCode Zen - Default)

```yaml
model_list:
  - model_name: glm-4.7-free
    litellm_params:
      api_base: https://opencode.ai/zen/v1
      api_key: "public"
```

### Local (llama.cpp)

```yaml
model_list:
  - model_name: qwen3-coder:a3b
    litellm_params:
      api_base: http://localhost:8080/v1
      api_key: "no-key-required"
      max_retries: 0  # Local - no retries needed
```

## OpenCode Configuration

Add to your `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "localcode": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "localcode",
      "options": {
        "baseURL": "http://localhost:4242/v1"
      },
      "models": {
        "glm-4.7-free": {
          "name": "GLM-4.7 Free",
          "limit": {
            "context": 204800,
            "output": 131072
          }
        }
      }
    }
  }
}
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /v1/chat/completions` | Chat completions (OpenAI-compatible) |
| `GET /v1/models` | List available models |
| `GET /health` | Health check |

## Log Output

The middleware prints structured logs:

### Request

```
================================================================================
[REQUEST] 12:34:56
Model: glm-4.7-free
Stream: False
Messages count: 1
================================================================================
```

### Response

```
--------------------------------------------------------------------------------
[RESPONSE] 12:34:58
Content: I'll help you edit the function...
Finish reason: stop
Usage - prompt: 150, completion: 45, total: 195
[Cached Tokens: 12]
--------------------------------------------------------------------------------
```

### Tool Call

```
[Tool Call] edit
[Tool Call] read
```

### Reasoning (GLM 4.7)

```
[STREAM CHUNK] 12:34:57 [REASONING] Let me think about this...
[STREAM CHUNK] 12:34:58 [REASONING] 1+1=2, so 2+2=4
[STREAM CHUNK] 12:34:59 4
```

## Architecture

Refactored from custom Python implementation to LiteLLM proxy:

| Before | After |
|--------|-------|
| 6 modules, ~736 lines | 3 files, ~50 lines |
| Custom HTTP client | Built-in LiteLLM router |
| Custom SSE parsing | `CustomStreamWrapper` |
| No retry logic | `max_retries`, `retry_after` |
| No connection pooling | httpx client reuse |

### Files

- `config.yaml` - LiteLLM model configuration
- `main.py` - Server entrypoint
- `logging_callbacks.py` - Custom event logging
- `opencode.json` - OpenCode provider config

## License

Same as parent OpenCode project.
