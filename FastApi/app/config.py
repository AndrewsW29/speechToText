"""Typed settings. Secrets come from environment variables only (never hardcoded)."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VA_", env_file=None, extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"

    auth_enabled: bool = True
    oidc_issuer: str | None = None
    oidc_jwks_url: str | None = None
    oidc_audience: str | None = None

    max_audio_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    default_language: str | None = None  # profile default until per-user preferences (US7)
    intent_serving_url: str | None = None  # TF Serving base URL; unset disables the gate
    intent_model_name: str = "intent"
    intent_model_label: str | None = None  # TF Serving version label (e.g. champion)
    intent_model_dir: Path | None = None  # exported version dir with vocab/labels/temperature
    glossary_path: Path | None = None  # curated terms for post-ASR correction
    stt_engine: str = "whisper"
    whisper_model_size: str = "small"

    qdrant_url: str | None = None  # ":memory:" for local mode; unset keeps the walking skeleton
    qdrant_collection: str = "code_knowledge"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    ingest_allowed_hosts: list[str] = Field(default_factory=list)
    ingestion_backend: str = "inline"  # "inline" or "celery"

    database_url: SecretStr | None = None
    redis_url: SecretStr | None = None

    otel_service_name: str = "voice-assistant-api"


@lru_cache
def get_settings() -> Settings:
    return Settings()
