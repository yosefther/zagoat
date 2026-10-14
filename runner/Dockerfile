# Runner services (mock LLM; the worker can run from it too). Build from runner/:
#   docker build -t zagoat-runner:dev .
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY mockllm ./mockllm
COPY zagoat_runner ./zagoat_runner
COPY harness ./harness

RUN useradd --uid 10002 --no-create-home --shell /usr/sbin/nologin runner
USER 10002:10002
ENV PROBLEMS_DIR=/srv/problems
EXPOSE 8090
CMD ["python", "-m", "mockllm", "--host", "0.0.0.0", "--port", "8090"]
