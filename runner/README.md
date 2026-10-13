# runner

Runs user code against a task's tests and grades it. This service runs on its own server
and must never hold database or payment credentials (brief, sections 4 and 5).

| Path | What it holds |
| --- | --- |
| `harness/zagoat/` | The `zagoat` package available inside the sandbox: `data_path`, `record_metric`, `llm_calls`, and the pytest plugin that records outcomes |
| `mockllm/` | The OpenAI-compatible mock LLM (`uv run python -m mockllm`) |
| `zagoat_runner/grading.py` | Turns what happened in the sandbox into a verdict |
| `zagoat_runner/executor.py` | The `Executor` interface and `LocalExecutor` (no isolation; CI and tests only) |
| `zagoat_runner/validate.py` | CI task validation |
| `zagoat_runner/config.py` | Every sandbox limit and timeout |

```sh
uv sync
uv run pytest
uv run python -m zagoat_runner.validate ../problems
```
