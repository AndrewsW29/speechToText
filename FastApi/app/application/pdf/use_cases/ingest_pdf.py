"""The ingestion saga: scan, inspect, read, index. Idempotent steps, compensation on failure."""

from __future__ import annotations

import logging
from dataclasses import asdict

from app.application.errors import (
    MalwareFoundError,
    NotAPdfError,
    ReaderNotConfiguredError,
    TooManyPagesError,
)
from app.application.pdf.ports.document_repository import DocumentRepository
from app.application.pdf.ports.event_publisher import EventPublisher
from app.application.pdf.ports.malware_scanner import MalwareScanner
from app.application.pdf.ports.object_store import ObjectStore
from app.application.pdf.ports.pdf_inspector import ActiveContentStripper, Inspection, PdfInspector
from app.application.pdf.ports.pipeline_stages import DocumentIndexer, DocumentReader
from app.application.pdf.services.step_ledger import StepLedger
from app.domain.pdf.document import Document, DocumentStatus

logger = logging.getLogger(__name__)

FAILURE_CODES: dict[type[Exception], str] = {
    NotAPdfError: "not_a_pdf",
    TooManyPagesError: "too_many_pages",
    ReaderNotConfiguredError: "reader_not_configured",
}


class IngestPdf:
    """Depends only on ports. Events: scanning, inspecting, reading, indexing, ready (or failed)."""

    def __init__(
        self,
        store: ObjectStore,
        scanner: MalwareScanner,
        inspector: PdfInspector,
        stripper: ActiveContentStripper,
        reader: DocumentReader,
        indexer: DocumentIndexer,
        repository: DocumentRepository,
        events: EventPublisher,
        ledger: StepLedger,
        max_pages: int = 1000,
        strip_active_content: bool = False,
    ) -> None:
        self._store, self._scanner, self._inspector, self._stripper = (
            store,
            scanner,
            inspector,
            stripper,
        )
        self._reader, self._indexer, self._repo, self._events = reader, indexer, repository, events
        self._ledger, self._max_pages, self._strip = ledger, max_pages, strip_active_content

    def execute(self, document_id: str) -> None:
        document = self._repo.get(document_id)
        if document is None:
            raise LookupError(f"unknown document {document_id}")
        try:
            self._run(document)
        except MalwareFoundError as exc:
            self._finish(document, DocumentStatus.QUARANTINED, f"malware: {exc}", "quarantined")
            raise
        except Exception as exc:
            self._compensate(document)
            reason = next(
                (code for kind, code in FAILURE_CODES.items() if isinstance(exc, kind)), None
            )
            self._finish(
                document, DocumentStatus.FAILED, reason or f"{type(exc).__name__}: {exc}", "failed"
            )
            raise

    # ------------------------------------------------------------------ steps
    def _run(self, document: Document) -> None:
        document = self._advance(document, DocumentStatus.SCANNING, "scanning")
        data = self._store.get(document.object_key)

        def scan() -> dict[str, object]:
            result = self._scanner.scan(data)
            if not result.clean:
                raise MalwareFoundError(result.signature or "unknown")
            return {"clean": True}

        self._ledger.run(document, "scan", scan)

        self._events.publish(document.id, "inspecting")
        inspection = Inspection(
            **{
                **(
                    found := self._ledger.run(
                        document, "inspect", lambda: self._inspect_to_dict(data)
                    )
                ),
                "active_content": frozenset(found["active_content"]),
            }
        )
        if inspection.encrypted:
            self._finish(document, DocumentStatus.FAILED, "password_required", "failed")
            return
        if inspection.page_count > self._max_pages:
            raise TooManyPagesError(f"{inspection.page_count} pages (limit {self._max_pages})")

        flags = sorted(inspection.active_content)
        if flags:
            document = document.with_flags("active_content_ignored", *flags)
            if self._strip:
                data = self._stripper.strip(data)
        document = self._repo_save(document.with_pages(inspection.page_count))

        document = self._advance(
            document,
            DocumentStatus.READING,
            "reading",
            pages_done=0,
            pages_total=inspection.page_count,
        )
        result = self._reader.read(document, data, inspection)

        self._events.publish(document.id, "indexing", pages_total=inspection.page_count)
        chunks = self._indexer.index(document, result)
        self._repo_save(document.with_status(DocumentStatus.READY))
        self._events.publish(document.id, "ready", pages_total=inspection.page_count, chunks=chunks)

    def _inspect_to_dict(self, data: bytes) -> dict[str, object]:
        found = asdict(self._inspector.inspect(data))
        found["active_content"] = sorted(found["active_content"])
        return found

    # ------------------------------------------------------------------ helpers
    def _advance(
        self, document: Document, status: DocumentStatus, stage: str, **fields: object
    ) -> Document:
        document = self._repo_save(document.with_status(status))
        self._events.publish(document.id, stage, **fields)
        return document

    def _repo_save(self, document: Document) -> Document:
        self._repo.save(document)
        return document

    def _finish(self, document: Document, status: DocumentStatus, reason: str, stage: str) -> None:
        current = self._repo.get(document.id) or document
        self._repo.save(current.with_status(status, reason))
        self._events.publish(
            document.id, stage, reason=reason.split(":")[0] if stage == "quarantined" else reason
        )

    def _compensate(self, document: Document) -> None:
        """Saga compensation: never leave a half-built version searchable."""
        try:
            self._indexer.delete_version(document.id, document.version)
        except Exception:
            logger.exception("compensation failed for %s", document.id)
