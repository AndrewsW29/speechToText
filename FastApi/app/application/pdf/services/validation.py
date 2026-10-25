"""Cheap, parser-free checks that run before any expensive work (F2)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.application.errors import NotAPdfError, QuotaExceededError, TooLargeError
from app.config import Settings

MAGIC = b"%PDF-"
MAGIC_WINDOW = 1024  # readers tolerate a short preamble before the header


@dataclass(frozen=True, slots=True)
class PdfLimits:
    max_file_bytes: int
    max_documents: int
    max_pages_per_day: int
    max_storage_bytes: int
    max_pages: int = 1000

    @classmethod
    def from_settings(cls, settings: Settings) -> PdfLimits:
        limits, quotas = settings.pdf_ingest.limits, settings.pdf_quotas
        return cls(
            max_file_bytes=limits.max_file_mb * 1024 * 1024,
            max_documents=quotas.max_documents,
            max_pages_per_day=quotas.max_pages_per_day,
            max_storage_bytes=quotas.max_storage_mb * 1024 * 1024,
            max_pages=limits.max_pages,
        )


@dataclass(frozen=True, slots=True)
class Usage:
    documents: int
    pages_today: int
    storage_bytes: int


@dataclass(frozen=True, slots=True)
class ValidatedUpload:
    sha256: str
    size: int


def validate_content(data: bytes, limits: PdfLimits) -> ValidatedUpload:
    """Magic bytes win over the extension and Content-Type, which are never trusted."""
    if (
        len(data) > limits.max_file_bytes
    ):  # also covers callers that stop reading at limit + 1 bytes
        raise TooLargeError(f"The file is larger than {limits.max_file_bytes // (1024 * 1024)} MB")
    if not data or MAGIC not in data[:MAGIC_WINDOW]:
        raise NotAPdfError
    return ValidatedUpload(hashlib.sha256(data).hexdigest(), len(data))


def enforce_quota(size: int, limits: PdfLimits, usage: Usage) -> None:
    if usage.documents >= limits.max_documents:
        raise QuotaExceededError("You have reached the maximum number of documents")
    if usage.pages_today >= limits.max_pages_per_day:
        raise QuotaExceededError("You have reached today's page limit; try again tomorrow")
    if usage.storage_bytes + size > limits.max_storage_bytes:
        raise QuotaExceededError("You have reached your storage limit")


def validate_upload(
    data: bytes,
    limits: PdfLimits,
    usage: Usage,
    filename: str | None = None,
    content_type: str | None = None,
) -> ValidatedUpload:
    """`filename` and `content_type` are accepted only so callers cannot be tempted to use them."""
    del filename, content_type
    validated = validate_content(data, limits)
    enforce_quota(validated.size, limits, usage)
    return validated
