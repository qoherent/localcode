"""LocalCode Middleware Server - Entry point."""

import asyncio
import client
from config import load_config, is_zen_backend
from logger import log_event
from server import create_app
from processor import (
    extract_request_info,
    categorize_delta,
    extract_message_parts,
    extract_usage_stats,
    get_finish_reason,
)
import uvicorn


def print_banner(config: dict, selected_model: str | None):
    """Print startup banner."""
    print("\n" + "#" * 80)
    print("# LocalCode Middleware Server")
    print(f"# Listening on http://0.0.0.0:{config['port']}")
    print(f"# Backend: {config['backend_url']}")
    if selected_model:
        print(f"# Selected Model: {selected_model} (auto-detected)")
    print("#" * 80 + "\n")


def main():
    """Main entry point."""
    config = load_config()

    backend_url = config["backend_url"]

    selected_model = None
    if is_zen_backend(backend_url):
        selected_model = asyncio.run(client.select_free_model(backend_url))

    print_banner(config, selected_model)

    processor = {
        "extract_request_info": extract_request_info,
        "categorize_delta": categorize_delta,
        "extract_message_parts": extract_message_parts,
        "extract_usage_stats": extract_usage_stats,
        "get_finish_reason": get_finish_reason,
    }

    app = create_app(
        backend_url=backend_url,
        log_event=log_event,
        post_chat_completions=client.post_chat_completions,
        processor=processor,
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config["port"],
        log_level=config["log_level"].lower(),
    )


if __name__ == "__main__":
    main()
