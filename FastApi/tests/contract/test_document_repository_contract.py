"""Behaviour every DocumentRepository/StepStore must have, in memory and on a real database."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from app.adapters.outbound.postgres.document_repository import SqlDocumentRepository, create_schema
from app.domain.pdf.document import Document, DocumentStatus
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from tests.fakes.pdf import InMemoryDocuments


def _doc(i: int, owner: str = "user:a", **kw) -> Document:  # type: ignore[no-untyped-def]
    return Document(f"d_{i}", owner, f"doc {i}", f"{i:064x}", f"sha256/{i}", **kw)


@pytest.fixture(params=["memory", "sql"])
def repo(request: pytest.FixtureRequest) -> Iterator:  # type: ignore[type-arg]
    if request.param == "memory":
        yield InMemoryDocuments()
        return
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_schema(engine)
    yield SqlDocumentRepository(engine)
    engine.dispose()


def test_add_get_and_save_roundtrip(repo) -> None:  # type: ignore[no-untyped-def]
    repo.add(_doc(1, size_bytes=1234))
    loaded = repo.get("d_1")
    assert (
        loaded is not None
        and loaded.title == "doc 1"
        and loaded.size_bytes == 1234
        and loaded.flags == ()
    )
    repo.save(loaded.with_status(DocumentStatus.READY).with_pages(7).with_flags("javascript"))
    again = repo.get("d_1")
    assert (
        again.status is DocumentStatus.READY and again.pages == 7 and again.flags == ("javascript",)
    )
    assert repo.get("d_missing") is None


def test_find_by_hash_is_scoped_to_the_owner(repo) -> None:  # type: ignore[no-untyped-def]
    repo.add(_doc(1, "user:a"))
    assert repo.find_by_hash("user:a", f"{1:064x}").id == "d_1"
    assert repo.find_by_hash("user:b", f"{1:064x}") is None


def test_list_for_filters_by_owner_and_status(repo) -> None:  # type: ignore[no-untyped-def]
    repo.add(_doc(1))
    repo.add(_doc(2).with_status(DocumentStatus.READY))
    repo.add(_doc(3, "user:b"))
    assert {d.id for d in repo.list_for("user:a")} == {"d_1", "d_2"}
    assert [d.id for d in repo.list_for("user:a", DocumentStatus.READY)] == ["d_2"]


def test_usage_counts_documents_storage_and_todays_pages(repo) -> None:  # type: ignore[no-untyped-def]
    repo.add(_doc(1, size_bytes=100).with_pages(10))
    repo.add(_doc(2, size_bytes=50).with_pages(5))
    repo.add(_doc(3, "user:b", size_bytes=999).with_pages(99))
    old = _doc(4, created_at=datetime.now(UTC) - timedelta(days=2), size_bytes=10).with_pages(40)
    repo.add(old)
    usage = repo.usage("user:a")
    assert (usage.documents, usage.storage_bytes, usage.pages_today) == (3, 160, 15)


def test_steps_roundtrip_and_overwrite_by_key(repo) -> None:  # type: ignore[no-untyped-def]
    repo.add(_doc(1))
    assert repo.get_step("d_1:1:scan:v1") is None
    repo.put_step("d_1:1:scan:v1", "d_1", {"clean": True})
    assert repo.get_step("d_1:1:scan:v1") == {"clean": True}
    repo.put_step("d_1:1:scan:v1", "d_1", {"clean": True, "n": 2})
    assert repo.get_step("d_1:1:scan:v1")["n"] == 2


def test_dead_letters_are_recorded(repo) -> None:  # type: ignore[no-untyped-def]
    repo.add(_doc(1))
    repo.dead_letter("d_1", "ScannerUnavailableError", 3)
    letters = getattr(repo, "dead_letters", None)
    if letters is not None:
        assert letters == [("d_1", "ScannerUnavailableError", 3)]
    else:
        assert repo.dead_letter_rows() == [("d_1", "ScannerUnavailableError", 3)]
