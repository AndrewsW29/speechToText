# Pin by digest in CI: python:3.13-slim@sha256:<digest> (resolve with `docker buildx imagetools inspect`).
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
WORKDIR /srv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --extra stt --extra embeddings
COPY app ./app
COPY ml/glossary ./ml/glossary
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv sync --frozen --no-dev --extra stt --extra embeddings

FROM python:3.13-slim AS runtime
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --no-create-home app
WORKDIR /srv
COPY --from=builder --chown=app:app /srv/.venv /srv/.venv
COPY --from=builder --chown=app:app /srv/app /srv/app
COPY --from=builder --chown=app:app /srv/ml/glossary /srv/ml/glossary
COPY --from=builder --chown=app:app /srv/alembic /srv/alembic
COPY --from=builder --chown=app:app /srv/alembic.ini /srv/alembic.ini
ENV VA_GLOSSARY_PATH=/srv/ml/glossary/terms.yaml PATH="/srv/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status == 200 else 1)"]
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
