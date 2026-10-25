# Training image. CPU by default; build with --build-arg GPU=true on a Linux node with an NVIDIA GPU
# (TensorFlow GPU support on macOS is limited). Pin the base by digest in CI.
FROM python:3.13-slim AS base
ARG GPU=false
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
WORKDIR /srv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 MLFLOW_DISABLE_AGENT_HINT=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --group ml \
 && if [ "$GPU" = "true" ]; then uv pip install "tensorflow[and-cuda]"; fi
COPY app ./app
COPY ml ./ml
RUN groupadd --system --gid 10001 trainer && useradd --system --uid 10001 --gid trainer --no-create-home trainer \
 && mkdir -p /srv/ml/artifacts && chown -R trainer:trainer /srv/ml/artifacts
ENV PATH="/srv/.venv/bin:$PATH"
USER 10001:10001
VOLUME ["/srv/ml/artifacts"]
# IMAGE_DIGEST and GIT_SHA are injected by CI so registration can record them.
ENTRYPOINT ["python", "-m", "ml.training.intent.pipeline"]
CMD ["--epochs", "30", "--seed", "7"]
