"""Configuration management for LocalCode Middleware."""

import os
from typing import Literal

from dotenv import load_dotenv


def load_config() -> dict:
    """Load configuration from .env file with defaults.

    Returns:
        Configuration dictionary with keys:
        - port: Server listening port
        - backend_url: Backend API URL (zen or llama.cpp)
        - log_level: Logging verbosity
    """
    load_dotenv()

    port_str = os.getenv("PORT", "4242")
    try:
        port = int(port_str)
    except ValueError:
        port = 4242

    backend_url = os.getenv("BACKEND_URL", "https://opencode.ai/zen/v1")

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_log_levels = {"DEBUG", "INFO", "WARN", "ERROR"}
    if log_level not in valid_log_levels:
        log_level = "INFO"

    return {
        "port": port,
        "backend_url": backend_url,
        "log_level": log_level,
    }


def get_config() -> dict:
    """Get current configuration (immutable after load)."""
    return load_config()


def is_zen_backend(backend_url: str) -> bool:
    """Check if backend URL points to zen."""
    return "opencode.ai" in backend_url
