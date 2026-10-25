"""Document aggregate. Pure domain: no framework imports."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


class DocumentStatus(StrEnum):
    QUEUED = "queued"
    SCANNING = "scanning"
    READING = "reading"
    PARTIAL = "partial"
    READY = "ready"
    FAILED = "failed"
    QUARANTINED = "quarantined"


TERMINAL = frozenset({DocumentStatus.READY, DocumentStatus.FAILED, DocumentStatus.QUARANTINED})


def new_document_id() -> str:
    return f"d_{uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    owner: str
    title: str
    sha256: str
    object_key: str
    status: DocumentStatus = DocumentStatus.QUEUED
    version: int = 1
    pages: int | None = None
    flags: tuple[str, ...] = ()
    failure_reason: str | None = None
    size_bytes: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.owner.strip():
            raise ValueError("document needs an id and an owner")
        if len(self.sha256) != 64:
            raise ValueError("sha256 must be a hex digest")
        if self.version < 1:
            raise ValueError("version starts at 1")

    def with_status(self, status: DocumentStatus, reason: str | None = None) -> Document:
        return replace(self, status=status, failure_reason=reason if status in TERMINAL else None)

    def with_flags(self, *flags: str) -> Document:
        return replace(self, flags=tuple(sorted({*self.flags, *flags})))

    def with_pages(self, pages: int) -> Document:
        return replace(self, pages=pages)

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL


PUBLIC_REASONS = frozenset(
    {
        "not_a_pdf",
        "too_many_pages",
        "password_required",
        "reader_not_configured",
        "queue_unavailable",
        "malware",
    }
)


def public_reason(reason: str | None) -> str | None:
    """What users may see: a stable code, never an internal message."""
    if reason is None:
        return None
    code = reason.split(":", 1)[0]
    return code if code in PUBLIC_REASONS else "processing_error"
