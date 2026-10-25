"""In-memory doubles for every PDF port."""

from __future__ import annotations

import hashlib
import threading
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from app.application.errors import ScannerUnavailableError, StorageError
from app.application.pdf.ports.document_repository import DocumentRepository, OwnerUsage, StepStore
from app.application.pdf.ports.event_publisher import EventPublisher, EventReader
from app.application.pdf.ports.malware_scanner import MalwareScanner, ScanResult
from app.application.pdf.ports.object_store import ObjectStore
from app.application.pdf.ports.pdf_inspector import ActiveContentStripper, Inspection, PdfInspector
from app.application.pdf.ports.pipeline_stages import (
    DocumentIndexer,
    DocumentReader,
    PipelineLauncher,
    ReadResult,
)
from app.domain.pdf.document import Document, DocumentStatus

from tests.pdf_fixtures import EICAR


class InMemoryObjectStore(ObjectStore):
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.put_count = 0
        self.fail_next = 0

    def put(self, data: bytes) -> str:
        if self.fail_next:
            self.fail_next -= 1
            raise StorageError("storage hiccup")
        key = "sha256/" + hashlib.sha256(data).hexdigest()
        if key not in self.objects:
            self.objects[key] = data
            self.put_count += 1
        return key

    def get(self, key: str) -> bytes:
        try:
            return self.objects[key]
        except KeyError:
            raise StorageError(f"missing object {key}") from None

    def exists(self, key: str) -> bool:
        return key in self.objects

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)


class InMemoryDocuments(DocumentRepository, StepStore):
    def __init__(self) -> None:
        self._docs: dict[str, Document] = {}
        self._steps: dict[str, dict[str, Any]] = {}
        self.dead_letters: list[tuple[str, str, int]] = []
        self._sizes: dict[str, int] = {}
        self._lock = threading.Lock()

    def add(self, document: Document) -> None:
        with self._lock:
            self._docs[document.id] = document

    def get(self, document_id: str) -> Document | None:
        return self._docs.get(document_id)

    def find_by_hash(self, owner: str, sha256: str) -> Document | None:
        return next(
            (d for d in self._docs.values() if d.owner == owner and d.sha256 == sha256), None
        )

    def list_for(self, owner: str, status: DocumentStatus | None = None) -> Sequence[Document]:
        return [
            d
            for d in self._docs.values()
            if d.owner == owner and (status is None or d.status == status)
        ]

    def save(self, document: Document) -> None:
        with self._lock:
            self._docs[document.id] = document

    def usage(self, owner: str) -> OwnerUsage:
        mine = [d for d in self._docs.values() if d.owner == owner]
        today = datetime.now(UTC).date()
        return OwnerUsage(
            documents=len(mine),
            pages_today=sum(d.pages or 0 for d in mine if d.created_at.date() == today),
            storage_bytes=sum(d.size_bytes for d in mine),
        )

    def dead_letter(self, document_id: str, reason: str, attempts: int) -> None:
        self.dead_letters.append((document_id, reason, attempts))

    def all(self) -> list[Document]:
        return list(self._docs.values())

    def get_step(self, key: str) -> dict[str, Any] | None:
        return self._steps.get(key)

    def put_step(self, key: str, document_id: str, result: dict[str, Any]) -> None:
        self._steps[key] = result

    def steps(self) -> list[str]:
        return list(self._steps)


class FakeLauncher(PipelineLauncher):
    def __init__(self, fail: bool = False) -> None:
        self.launched: list[str] = []
        self._fail = fail

    def launch(self, document_id: str) -> None:
        if self._fail:
            raise RuntimeError("broker down")
        self.launched.append(document_id)


class FakeScanner(MalwareScanner):
    """Flags the EICAR test string; `down` simulates an unreachable scanner."""

    def __init__(self, down: bool = False) -> None:
        self.down = down
        self.scans = 0

    def scan(self, data: bytes) -> ScanResult:
        self.scans += 1
        if self.down:
            raise ScannerUnavailableError("scanner is down")
        if EICAR in data:
            return ScanResult(False, "Eicar-Test-Signature")
        return ScanResult(True)


class FakeInspector(PdfInspector, ActiveContentStripper):
    def __init__(
        self, pages: int = 3, active: frozenset[str] = frozenset(), encrypted: bool = False
    ) -> None:
        self._inspection = Inspection(pages, encrypted, active)
        self.calls = 0
        self.stripped = 0

    def inspect(self, data: bytes) -> Inspection:
        self.calls += 1
        return self._inspection

    def strip(self, data: bytes) -> bytes:
        self.stripped += 1
        return data


class FakeReader(DocumentReader):
    def __init__(self, fail_with: Exception | None = None) -> None:
        self.calls = 0
        self._fail = fail_with

    def read(self, document: Document, data: bytes, inspection: Inspection) -> ReadResult:
        self.calls += 1
        if self._fail:
            raise self._fail
        return ReadResult(
            pages_read=inspection.page_count,
            payload=[f"p{i}" for i in range(inspection.page_count)],
        )


class FakeIndexer(DocumentIndexer):
    """Upserts by deterministic id, so repeated indexing never duplicates."""

    def __init__(self, fail_times: int = 0, fail_with: Exception | None = None) -> None:
        self.chunks: dict[tuple[str, int, str], str] = {}
        self.index_calls = 0
        self.deleted: list[tuple[str, int]] = []
        self._fail_times = fail_times
        self._fail_with = fail_with or RuntimeError("embedder crashed")

    def index(self, document: Document, result: ReadResult) -> int:
        self.index_calls += 1
        for i, item in enumerate(result.payload):
            self.chunks[(document.id, document.version, f"{i}:{item}")] = str(item)
        if self._fail_times:
            self._fail_times -= 1
            raise self._fail_with
        return len(result.payload)

    def delete_version(self, document_id: str, version: int) -> None:
        self.deleted.append((document_id, version))
        for key in [k for k in self.chunks if k[0] == document_id and k[1] == version]:
            del self.chunks[key]


class InMemoryEvents(EventPublisher, EventReader):
    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = {}

    def publish(self, document_id: str, stage: str, **fields: Any) -> None:
        items = self._events.setdefault(document_id, [])
        items.append({"seq": len(items) + 1, "document_id": document_id, "stage": stage, **fields})

    def read(self, document_id: str, after: int = 0) -> list[dict[str, Any]]:
        return [e for e in self._events.get(document_id, []) if e["seq"] > after]

    def stages(self, document_id: str) -> list[str]:
        return [e["stage"] for e in self._events.get(document_id, [])]


__all__ = ["replace"]
