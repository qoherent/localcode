import argparse
import os
import signal
import sys

import uvicorn

import logging_callbacks  # noqa: F401 - Registers callbacks on import

from litellm.proxy.proxy_cli import run_server


def getenv(key: str, default: str) -> str:
    """Get environment variable or default."""
    return os.getenv(key, default)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LocalCode Middleware Server (powered by LiteLLM)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=getenv("LITELLM_CONFIG", "config.yaml"),
        help="Path to LiteLLM config file (default: config.yaml)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(getenv("LITELLM_PORT", "4242")),
        help="Server port (default: 4242)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=getenv("LITELLM_HOST", "0.0.0.0"),
        help="Server host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--loglevel",
        type=str,
        default=getenv("LITELLM_LOGLEVEL", "INFO"),
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    config_path = args.config
    port = args.port
    host = args.host

    print("\n" + "#" * 80)
    print("# LocalCode Middleware Server")
    print(f"# Powered by LiteLLM")
    print(f"# Config: {config_path}")
    print(f"# Listening on http://{host}:{port}")
    print("#" * 80 + "\n")

    def signal_handler(signum, frame):
        print("\n\nShutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    sys.argv = [
        "litellm",
        "--config",
        config_path,
        "--port",
        str(port),
        "--host",
        host,
    ]

    run_server()


if __name__ == "__main__":
    main()
