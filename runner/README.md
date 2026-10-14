# runner

Runs user code against a task's tests and grades it. This service runs on its own server
and must never hold database or payment credentials (brief, sections 4 and 5).

| Path | What it holds |
| --- | --- |
| `harness/zagoat/` | The `zagoat` package available inside the sandbox: `data_path`, `record_metric`, `llm_calls`, and the pytest plugin that records outcomes |
| `mockllm/` | The OpenAI-compatible mock LLM (`uv run python -m mockllm`) |
| `zagoat_runner/grading.py` | Turns what happened in the sandbox into a verdict |
| `zagoat_runner/executor.py` | The `Executor` interface and `LocalExecutor` (no isolation; CI and tests only) |
| `zagoat_runner/sandbox.py` | `DockerExecutor`: every limit and hardening rule from the brief |
| `zagoat_runner/worker.py` | Pulls jobs from Redis, runs them, posts results to the API |
| `images/py312-ml/` | The task image: Python 3.12, numpy, openai, pytest and the harness |
| `Dockerfile` | Image for the runner services (the mock LLM in docker compose) |
| `zagoat_runner/validate.py` | CI task validation |
| `zagoat_runner/config.py` | Every sandbox limit and timeout |

```sh
uv sync
uv run pytest
uv run python -m zagoat_runner.validate ../problems
docker build -f images/py312-ml/Dockerfile -t zagoat-py312-ml:dev .
uv run python -m zagoat_runner.worker
```

Production pins task images by digest (`IMAGES` in `.env`) and refuses to start without
gVisor (`runsc`). Locally, missing gVisor only prints a warning.
