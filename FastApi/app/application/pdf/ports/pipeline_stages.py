"""Stage ports the ingestion use case depends on; real readers and indexers arrive in US18/US19."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.application.pdf.ports.pdf_inspector import Inspection
from app.domain.pdf.document import Document


@dataclass(frozen=True, slots=True)
class ReadResult:
    pages_read: int
    payload: Any = None  # blocks, produced by the reader and consumed by the indexer


class DocumentReader(ABC):
    @abstractmethod
    def read(self, document: Document, data: bytes, inspection: Inspection) -> ReadResult: ...


class DocumentIndexer(ABC):
    @abstractmethod
    def index(self, document: Document, result: ReadResult) -> int:
        """Chunk, embed and upsert; returns the number of chunks. Must be idempotent."""

    @abstractmethod
    def delete_version(self, document_id: str, version: int) -> None: ...


class PipelineLauncher(ABC):
    @abstractmethod
    def launch(self, document_id: str) -> None: ...
