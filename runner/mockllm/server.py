"""Run the mock LLM in a background thread (task validation and tests)."""

import socket
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import uvicorn

from mockllm.app import create_app


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def background_mock_llm(problems_dir: Path) -> Iterator[str]:
    """Serve the mock LLM on a free local port and yield its OpenAI base URL."""
    port = free_port()
    config = uvicorn.Config(
        create_app(problems_dir), host="127.0.0.1", port=port, log_level="warning"
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("mock LLM did not start")
        time.sleep(0.05)
    try:
        yield f"http://127.0.0.1:{port}/v1"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
