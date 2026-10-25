from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.domain.pdf.document import Document, DocumentStatus


@dataclass(frozen=True, slots=True)
class OwnerUsage:
    documents: int
    pages_today: int
    storage_bytes: int


class DocumentRepository(ABC):
    @abstractmethod
    def add(self, document: Document) -> None: ...

    @abstractmethod
    def get(self, document_id: str) -> Document | None: ...

    @abstractmethod
    def find_by_hash(self, owner: str, sha256: str) -> Document | None: ...

    @abstractmethod
    def list_for(self, owner: str, status: DocumentStatus | None = None) -> Sequence[Document]: ...

    @abstractmethod
    def save(self, document: Document) -> None: ...

    @abstractmethod
    def usage(self, owner: str) -> OwnerUsage: ...

    @abstractmethod
    def dead_letter(self, document_id: str, reason: str, attempts: int) -> None: ...


class StepStore(ABC):
    """Records completed pipeline steps so a retry resumes instead of redoing work."""

    @abstractmethod
    def get_step(self, key: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def put_step(self, key: str, document_id: str, result: dict[str, Any]) -> None: ...
