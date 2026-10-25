# PDF ingestion worker: parses untrusted files, so it runs non-root with a read-only root filesystem.
# Run it with:  --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges
# Network: it needs Redis, Postgres, MinIO and ClamAV only; the parsing subprocess denies network on its own.
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
WORKDIR /srv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app
RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime
RUN groupadd --system --gid 10002 pdf && useradd --system --uid 10002 --gid pdf --no-create-home pdf
WORKDIR /srv
COPY --from=builder --chown=pdf:pdf /srv/.venv /srv/.venv
COPY --from=builder --chown=pdf:pdf /srv/app /srv/app
ENV PATH="/srv/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TMPDIR=/tmp
USER 10002:10002
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD ["celery", "-A", "app.workers.pdf_worker", "inspect", "ping", "-d", "celery@%h", "--timeout", "8"]
CMD ["celery", "-A", "app.workers.pdf_worker", "worker", "-Q", "ingest", "--concurrency", "2", "--loglevel", "INFO", "--max-tasks-per-child", "20"]
