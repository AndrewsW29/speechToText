"""Composition for PDF ingestion, shared by the API and the Celery worker."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine, create_engine

from app.adapters.outbound.pdf.celery_launcher import CeleryPipelineLauncher
from app.adapters.outbound.pdf.clamav_scanner import ClamAvScanner
from app.adapters.outbound.pdf.inline_launcher import InlineLauncher
from app.adapters.outbound.pdf.local_object_store import LocalFileObjectStore
from app.adapters.outbound.pdf.memory_events import MemoryEvents
from app.adapters.outbound.pdf.minio_object_store import MinioObjectStore
from app.adapters.outbound.pdf.redis_events import RedisEvents
from app.adapters.outbound.pdf.sandbox import SandboxedPdfInspector, SandboxLimits, SandboxRunner
from app.adapters.outbound.pdf.unconfigured import UnconfiguredIndexer, UnconfiguredReader
from app.adapters.outbound.postgres.document_repository import SqlDocumentRepository, create_schema
from app.application.errors import ScannerUnavailableError
from app.application.pdf.ports.document_repository import DocumentRepository
from app.application.pdf.ports.event_publisher import EventPublisher, EventReader
from app.application.pdf.ports.malware_scanner import MalwareScanner, ScanResult
from app.application.pdf.ports.object_store import ObjectStore
from app.application.pdf.ports.pipeline_stages import PipelineLauncher
from app.application.pdf.services.step_ledger import StepLedger
from app.application.pdf.use_cases.ingest_pdf import IngestPdf
from app.application.pdf.use_cases.upload_document import UploadDocument
from app.config import Settings


class StartupError(RuntimeError):
    """The deployment is misconfigured in a way that must not be papered over."""


class DisabledScanner(MalwareScanner):
    """Only for local development with `scan_malware=false`. Never silently selected."""

    def scan(self, data: bytes) -> ScanResult:
        return ScanResult(clean=True)


@dataclass(frozen=True, slots=True)
class PdfServices:
    ingest: IngestPdf
    repository: DocumentRepository
    events_reader: EventReader
    events_publisher: EventPublisher


def sync_database_url(settings: Settings) -> str:
    if settings.database_url is not None:
        return settings.database_url.get_secret_value().replace("+asyncpg", "+psycopg")
    if settings.environment.lower() not in {"local", "test"}:
        raise StartupError(
            "VA_DATABASE_URL is required for PDF ingestion outside local environments"
        )
    settings.pdf_storage_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{settings.pdf_storage_dir.resolve() / 'documents.db'}"


def build_engine(settings: Settings) -> Engine:
    engine = create_engine(sync_database_url(settings), pool_pre_ping=True)
    if engine.dialect.name == "sqlite":
        create_schema(engine)  # production schemas come from Alembic
    return engine


def build_object_store(settings: Settings) -> ObjectStore:
    if settings.minio_endpoint:
        from minio import Minio

        if settings.minio_access_key is None or settings.minio_secret_key is None:
            raise StartupError(
                "MinIO credentials are not set (VA_MINIO_ACCESS_KEY / VA_MINIO_SECRET_KEY)"
            )
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key.get_secret_value(),
            secret_key=settings.minio_secret_key.get_secret_value(),
            secure=settings.minio_secure,
        )
        return MinioObjectStore(client, settings.minio_bucket)
    return LocalFileObjectStore(settings.pdf_storage_dir / "objects")


def build_scanner(settings: Settings) -> MalwareScanner:
    if not settings.pdf_ingest.security.scan_malware:
        return DisabledScanner()
    if not settings.clamav_host:
        raise StartupError(
            "malware scanning is enabled but VA_CLAMAV_HOST is not set (fail closed)"
        )
    return ClamAvScanner(settings.clamav_host, settings.clamav_port)


def build_events(settings: Settings) -> tuple[EventPublisher, EventReader]:
    if settings.redis_url is not None:
        from redis import Redis

        events = RedisEvents(Redis.from_url(settings.redis_url.get_secret_value()))
        return events, events
    memory = MemoryEvents()
    return memory, memory


def sandbox_limits(settings: Settings) -> SandboxLimits:
    limits = settings.pdf_ingest.limits
    return SandboxLimits(
        cpu_seconds=limits.per_doc_timeout_min * 60,
        wall_seconds=limits.per_doc_timeout_min * 60,
        max_pixels=50_000_000,
    )


def build_pdf_services(
    settings: Settings, events: tuple[EventPublisher, EventReader] | None = None
) -> PdfServices:
    repository = SqlDocumentRepository(build_engine(settings))
    publisher, reader = events or build_events(settings)
    inspector = SandboxedPdfInspector(SandboxRunner(), sandbox_limits(settings))
    security = settings.pdf_ingest.security
    ingest = IngestPdf(
        build_object_store(settings),
        build_scanner(settings),
        inspector,
        inspector,
        UnconfiguredReader(),
        UnconfiguredIndexer(),
        repository,
        publisher,
        StepLedger(repository, settings.pdf_ledger_pipeline_version),
        max_pages=settings.pdf_ingest.limits.max_pages,
        strip_active_content=security.strip_active_content,
    )
    return PdfServices(ingest, repository, reader, publisher)


def build_launcher(settings: Settings, services: PdfServices) -> PipelineLauncher:
    if settings.ingestion_backend == "celery":
        from app.workers.celery_app import celery_app
        from app.workers.pdf_tasks import make_pdf_tasks

        task = make_pdf_tasks(
            celery_app, lambda: worker_pipeline(settings), settings.pdf_max_retries
        )
        return CeleryPipelineLauncher(task)
    return InlineLauncher(services.ingest)


_WORKER: tuple[IngestPdf, DocumentRepository] | None = None


def worker_pipeline(settings: Settings) -> tuple[IngestPdf, DocumentRepository]:
    global _WORKER
    if _WORKER is None:
        services = build_pdf_services(settings)
        _WORKER = (services.ingest, services.repository)
    return _WORKER


def build_pdf_container_parts(settings: Settings) -> dict[str, object]:
    services = build_pdf_services(settings)
    upload = UploadDocument(
        services.ingest._store,
        services.repository,
        build_launcher(settings, services),
        settings,
    )
    return {
        "upload_document": upload,
        "documents": services.repository,
        "document_events": services.events_reader,
    }


__all__ = [
    "ScannerUnavailableError",
    "StartupError",
    "build_pdf_container_parts",
    "build_pdf_services",
]
