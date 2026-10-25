"""Celery tasks for PDF ingestion. Queues: `ingest` (CPU parsing), `gpu`, `learn` (low priority)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from celery import Celery

from app.application.errors import TransientError
from app.application.pdf.ports.document_repository import DocumentRepository
from app.application.pdf.services.retry_policy import backoff_seconds, is_transient
from app.application.pdf.use_cases.ingest_pdf import IngestPdf

QUEUE_ROUTES: dict[str, dict[str, str]] = {
    "pdf.ingest": {"queue": "ingest"},
    "pdf.ocr": {"queue": "gpu"},
    "pdf.layout": {"queue": "gpu"},
    "pdf.learn.*": {"queue": "learn"},
}
TASK_NAME = "pdf.ingest"


def process_document(
    ingest: IngestPdf,
    repository: DocumentRepository,
    document_id: str,
    retries: int,
    max_retries: int,
) -> tuple[str, float | None]:
    """One attempt: ("ok"|"failed"|"dead_lettered", None) or ("retry", countdown_seconds)."""
    try:
        ingest.execute(document_id)
        return "ok", None
    except LookupError:
        return "failed", None  # the document was deleted meanwhile
    except Exception as exc:
        if not is_transient(exc):
            return "failed", None
        if retries >= max_retries:
            repository.dead_letter(document_id, type(exc).__name__, retries + 1)
            return "dead_lettered", None
        return "retry", backoff_seconds(retries)


def make_pdf_tasks(
    app: Celery, factory: Callable[[], tuple[IngestPdf, DocumentRepository]], max_retries: int = 3
) -> Any:
    @app.task(name=TASK_NAME, bind=True)  # type: ignore[untyped-decorator]
    def ingest_document(self: Any, document_id: str) -> str:
        ingest, repository = factory()
        outcome, countdown = process_document(
            ingest, repository, document_id, self.request.retries, max_retries
        )
        if outcome == "retry":
            raise self.retry(countdown=countdown, exc=TransientError(document_id))
        return outcome

    return ingest_document


def configure_queues(app: Celery) -> None:
    app.conf.task_routes = {**(app.conf.task_routes or {}), **QUEUE_ROUTES}
    app.conf.task_queues_max_priority = 10
