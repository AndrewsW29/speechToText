"""Stage placeholders until the real reader (US18) and indexer (US19) are wired.

They fail loudly and permanently, so a document never looks ready without having been read.
"""

from __future__ import annotations

from app.application.errors import ReaderNotConfiguredError
from app.application.pdf.ports.pdf_inspector import Inspection
from app.application.pdf.ports.pipeline_stages import DocumentIndexer, DocumentReader, ReadResult
from app.domain.pdf.document import Document


class UnconfiguredReader(DocumentReader):
    def read(self, document: Document, data: bytes, inspection: Inspection) -> ReadResult:
        raise ReaderNotConfiguredError("no PDF reader is configured in this deployment")


class UnconfiguredIndexer(DocumentIndexer):
    def index(self, document: Document, result: ReadResult) -> int:
        raise ReaderNotConfiguredError("no PDF indexer is configured in this deployment")

    def delete_version(self, document_id: str, version: int) -> None:
        return None  # nothing was ever indexed
