"""Serve the mock LLM: python -m mockllm [--host H] [--port P] [--problems DIR]"""

import argparse
from pathlib import Path

import uvicorn

from mockllm.app import create_app
from zagoat_runner.config import get_settings


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(prog="python -m mockllm")
    parser.add_argument("--host", default=settings.mock_llm_host)
    parser.add_argument("--port", type=int, default=settings.mock_llm_port)
    parser.add_argument("--problems", type=Path, default=settings.problems_dir)
    args = parser.parse_args()
    uvicorn.run(create_app(args.problems), host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
