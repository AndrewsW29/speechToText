from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.errors import QueueUnavailableError, TransientError
from app.application.pdf.ports.document_repository import DocumentRepository
from app.application.pdf.ports.object_store import ObjectStore
from app.application.pdf.ports.pipeline_stages import PipelineLauncher
from app.application.pdf.services.validation import (
    PdfLimits,
    Usage,
    enforce_quota,
    validate_content,
)
from app.config import Settings
from app.domain.pdf.document import Document, DocumentStatus, new_document_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class UploadResult:
    document: Document
    duplicate_of: str | None = None


class UploadDocument:
    """Validate, deduplicate, store, register and enqueue; the heavy work is asynchronous."""

    def __init__(
        self,
        store: ObjectStore,
        repository: DocumentRepository,
        launcher: PipelineLauncher,
        settings: Settings,
    ) -> None:
        self._store = store
        self._repo = repository
        self._launcher = launcher
        self._limits = PdfLimits.from_settings(settings)

    def execute(
        self,
        owner: str,
        data: bytes,
        filename: str | None = None,
        content_type: str | None = None,
        title: str | None = None,
    ) -> UploadResult:
        del content_type  # never trusted: the magic bytes decide
        validated = validate_content(data, self._limits)
        if existing := self._repo.find_by_hash(owner, validated.sha256):
            return UploadResult(existing, duplicate_of=existing.id)

        usage = self._repo.usage(owner)
        enforce_quota(
            validated.size,
            self._limits,
            Usage(usage.documents, usage.pages_today, usage.storage_bytes),
        )
        key = self._store.put(data)
        document = Document(
            id=new_document_id(),
            owner=owner,
            title=(title or filename or "Untitled").strip()[:200] or "Untitled",
            sha256=validated.sha256,
            object_key=key,
            size_bytes=validated.size,
        )
        self._repo.add(document)
        try:
            self._launcher.launch(document.id)
        except Exception as exc:
            logger.exception("could not queue document %s", document.id)
            self._repo.save(document.with_status(DocumentStatus.FAILED, "queue_unavailable"))
            raise QueueUnavailableError(
                "The processing queue is unavailable, please retry"
            ) from exc
        return UploadResult(document)


__all__ = ["TransientError", "UploadDocument", "UploadResult"]
