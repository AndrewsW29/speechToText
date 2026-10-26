"""Typed settings. Secrets come from environment variables only (never hardcoded)."""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PdfLimitSettings(BaseModel):
    max_file_mb: int = 50
    max_pages: int = 1000
    per_page_timeout_s: int = 30
    per_doc_timeout_min: int = 20


class PdfOcrSettings(BaseModel):
    dpi: int = 300
    min_confidence: float = 0.80
    languages: list[str] = Field(default_factory=lambda: ["eng"])


class PdfChunkingSettings(BaseModel):
    max_tokens: int = 350
    overlap_tokens: int = 40
    parent_tokens: int = 900
    code_max_tokens: int = 500


class PdfRetrievalSettings(BaseModel):
    dense_top: int = 50
    sparse_top: int = 50
    fused_top: int = 20
    final_top: int = 5


class PdfSecuritySettings(BaseModel):
    scan_malware: bool = True
    ignore_active_content: bool = True
    strip_active_content: bool = False
    quarantine_hidden_text: bool = True
    respect_copy_restrictions: bool = True


class PdfLearningSettings(BaseModel):
    mine_glossary: bool = True
    synthetic_qa: bool = True
    use_for_training: bool = False


class PdfIngestSettings(BaseModel):
    """Defaults from READ_LEARN_FEATURE.md section 8; every value is tunable by environment."""

    limits: PdfLimitSettings = Field(default_factory=PdfLimitSettings)
    ocr: PdfOcrSettings = Field(default_factory=PdfOcrSettings)
    chunking: PdfChunkingSettings = Field(default_factory=PdfChunkingSettings)
    retrieval: PdfRetrievalSettings = Field(default_factory=PdfRetrievalSettings)
    security: PdfSecuritySettings = Field(default_factory=PdfSecuritySettings)
    learning: PdfLearningSettings = Field(default_factory=PdfLearningSettings)


class PdfQuotas(BaseModel):
    max_documents: int = 500
    max_pages_per_day: int = 5000
    max_storage_mb: int = 2048


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VA_", env_file=None, extra="ignore", env_nested_delimiter="__"
    )

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
    llm_url: str | None = None  # Ollama base URL; unset serves retrieval-only snippet answers
    llm_model: str = "llama3.2"
    llm_timeout_seconds: float = Field(default=20.0, gt=0)
    llm_failure_threshold: int = Field(default=3, ge=1)
    llm_reset_seconds: float = Field(default=30.0, gt=0)
    glossary_path: Path | None = None  # curated terms for post-ASR correction
    stt_engine: str = "whisper"  # "whisper", or "fake" (CI, local and Postman only)
    fake_stt_text: str | None = None
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

    pdf_ingest: PdfIngestSettings = Field(default_factory=PdfIngestSettings)
    pdf_quotas: PdfQuotas = Field(default_factory=PdfQuotas)
    pdf_enabled: bool = (
        False  # PDF ingestion needs storage, a scanner and a queue: opt in explicitly
    )
    pdf_storage_dir: Path = Path(
        "data/pdf"
    )  # local originals and SQLite when MinIO/Postgres are not configured
    pdf_max_retries: int = 3
    pdf_events_poll_seconds: float = 0.25
    pdf_ledger_pipeline_version: str = "pdf-ingest@0.1.0"
    tus_hook_token: SecretStr | None = None
    tus_upload_dir: Path | None = None
    minio_endpoint: str | None = None
    minio_access_key: SecretStr | None = None
    minio_secret_key: SecretStr | None = None
    minio_bucket: str = "documents"
    minio_secure: bool = False
    clamav_host: str | None = None
    clamav_port: int = 3310

    otel_service_name: str = "voice-assistant-api"


@lru_cache
def get_settings() -> Settings:
    return Settings()
