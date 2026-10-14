# Sandbox image for Python tasks. Build from the runner/ folder:
#   docker build -f images/py312-ml/Dockerfile -t zagoat-py312-ml:dev .
# Production pins it by digest (IMAGES in runner/.env).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY images/py312-ml/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# The zagoat harness and helpers (data_path, record_metric, llm_calls).
COPY harness/zagoat /opt/zagoat/zagoat
ENV PYTHONPATH=/opt/zagoat

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin sandbox
USER 10001:10001
WORKDIR /work
