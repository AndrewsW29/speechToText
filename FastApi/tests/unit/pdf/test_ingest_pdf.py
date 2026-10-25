import pytest
from app.application.errors import (
    MalwareFoundError,
    NotAPdfError,
    ReaderNotConfiguredError,
    ScannerUnavailableError,
    TooManyPagesError,
)
from app.application.pdf.services.step_ledger import StepLedger
from app.application.pdf.use_cases.ingest_pdf import IngestPdf
from app.domain.pdf.document import Document, DocumentStatus

from tests.fakes.pdf import (
    FakeIndexer,
    FakeInspector,
    FakeReader,
    FakeScanner,
    InMemoryDocuments,
    InMemoryEvents,
    InMemoryObjectStore,
)
from tests.pdf_fixtures import EICAR, build_pdf


class Rig:
    def __init__(self, data: bytes | None = None, **overrides) -> None:  # type: ignore[no-untyped-def]
        self.data = data or build_pdf(3)
        self.store, self.repo, self.events = (
            InMemoryObjectStore(),
            InMemoryDocuments(),
            InMemoryEvents(),
        )
        self.scanner = overrides.get("scanner") or FakeScanner()
        self.inspector = overrides.get("inspector") or FakeInspector(pages=3)
        self.reader = overrides.get("reader") or FakeReader()
        self.indexer = overrides.get("indexer") or FakeIndexer()
        key = self.store.put(self.data)
        import hashlib

        self.doc = Document(
            "d_1", "user:a", "guide.pdf", hashlib.sha256(self.data).hexdigest(), key
        )
        self.repo.add(self.doc)
        self.use_case = IngestPdf(
            self.store,
            self.scanner,
            self.inspector,
            self.inspector,
            self.reader,
            self.indexer,
            self.repo,
            self.events,
            StepLedger(self.repo, "pdf-ingest@test"),
            max_pages=overrides.get("max_pages", 1000),
            strip_active_content=overrides.get("strip", False),
        )

    def run(self) -> Document:
        self.use_case.execute("d_1")
        return self.repo.get("d_1")  # type: ignore[return-value]


def test_happy_path_goes_through_every_stage_and_ends_ready() -> None:
    rig = Rig()
    doc = rig.run()
    assert doc.status is DocumentStatus.READY and doc.pages == 3
    assert rig.events.stages("d_1") == ["scanning", "inspecting", "reading", "indexing", "ready"]
    ready = rig.events.read("d_1")[-1]
    assert ready["pages_total"] == 3 and ready["chunks"] == 3


def test_progress_events_carry_page_counters() -> None:
    rig = Rig()
    rig.run()
    reading = next(e for e in rig.events.read("d_1") if e["stage"] == "reading")
    assert reading["pages_total"] == 3


def test_infected_files_are_quarantined_and_never_parsed() -> None:
    rig = Rig(build_pdf() + EICAR)
    with pytest.raises(MalwareFoundError):
        rig.use_case.execute("d_1")
    doc = rig.repo.get("d_1")
    assert (
        doc.status is DocumentStatus.QUARANTINED
        and doc.failure_reason == "malware: Eicar-Test-Signature"
    )  # type: ignore[union-attr]
    assert rig.inspector.calls == 0 and rig.reader.calls == 0
    assert rig.events.stages("d_1")[-1] == "quarantined"


def test_an_unreachable_scanner_fails_closed_and_is_retryable() -> None:
    rig = Rig(scanner=FakeScanner(down=True))
    with pytest.raises(ScannerUnavailableError):
        rig.use_case.execute("d_1")
    assert rig.reader.calls == 0 and rig.repo.get("d_1").status is DocumentStatus.FAILED  # type: ignore[union-attr]


def test_active_content_is_flagged_not_executed_and_the_document_still_reads() -> None:
    rig = Rig(inspector=FakeInspector(pages=2, active=frozenset({"javascript", "launch"})))
    doc = rig.run()
    assert doc.status is DocumentStatus.READY and set(doc.flags) == {
        "active_content_ignored",
        "javascript",
        "launch",
    }
    assert rig.inspector.stripped == 0


def test_optional_stripping_removes_active_content_before_reading() -> None:
    rig = Rig(inspector=FakeInspector(pages=2, active=frozenset({"javascript"})), strip=True)
    rig.run()
    assert rig.inspector.stripped == 1


def test_documents_over_the_page_limit_fail_without_reading() -> None:
    rig = Rig(inspector=FakeInspector(pages=50), max_pages=10)
    with pytest.raises(TooManyPagesError):
        rig.use_case.execute("d_1")
    assert rig.reader.calls == 0 and rig.repo.get("d_1").failure_reason == "too_many_pages"  # type: ignore[union-attr]


def test_encrypted_documents_wait_for_a_password_instead_of_failing() -> None:
    rig = Rig(inspector=FakeInspector(pages=0, encrypted=True))
    doc = rig.run()
    assert doc.status is DocumentStatus.FAILED and doc.failure_reason == "password_required"
    assert (
        "password_required" in rig.events.stages("d_1")[-1]
        or rig.events.read("d_1")[-1]["reason"] == "password_required"
    )


def test_a_failure_while_indexing_compensates_by_deleting_the_half_built_version() -> None:
    rig = Rig(indexer=FakeIndexer(fail_times=1))
    with pytest.raises(RuntimeError):
        rig.use_case.execute("d_1")
    assert rig.indexer.deleted == [("d_1", 1)] and rig.indexer.chunks == {}
    doc = rig.repo.get("d_1")
    assert doc.status is DocumentStatus.FAILED and "embedder crashed" in (doc.failure_reason or "")  # type: ignore[union-attr]
    assert rig.events.stages("d_1")[-1] == "failed"


def test_a_failed_document_leaves_no_partial_index_and_can_be_retried_to_success() -> None:
    rig = Rig(indexer=FakeIndexer(fail_times=1))
    with pytest.raises(RuntimeError):
        rig.use_case.execute("d_1")
    rig.use_case.execute("d_1")  # the retry
    assert rig.repo.get("d_1").status is DocumentStatus.READY  # type: ignore[union-attr]
    assert len(rig.indexer.chunks) == 3


def test_a_missing_reader_is_reported_as_not_configured() -> None:
    from app.application.pdf.ports.pipeline_stages import DocumentReader

    class Unconfigured(DocumentReader):
        def read(self, document, data, inspection):  # type: ignore[no-untyped-def]
            raise ReaderNotConfiguredError("no reader")

    rig = Rig(reader=Unconfigured())
    with pytest.raises(ReaderNotConfiguredError):
        rig.use_case.execute("d_1")
    assert rig.repo.get("d_1").failure_reason == "reader_not_configured"  # type: ignore[union-attr]


def test_not_a_pdf_inside_the_sandbox_is_a_permanent_failure() -> None:
    class Garbage(FakeInspector):
        def inspect(self, data):  # type: ignore[no-untyped-def]
            raise NotAPdfError

    rig = Rig(inspector=Garbage())
    with pytest.raises(NotAPdfError):
        rig.use_case.execute("d_1")
    assert rig.repo.get("d_1").failure_reason == "not_a_pdf"  # type: ignore[union-attr]
