import pytest
from app.application.errors import (
    MalwareFoundError,
    NotAPdfError,
    ScannerUnavailableError,
    StorageError,
    TransientError,
)
from app.application.pdf.services.retry_policy import backoff_seconds, is_transient
from app.application.pdf.services.step_ledger import StepLedger

from tests.fakes.pdf import FakeIndexer, FakeScanner
from tests.unit.pdf.test_ingest_pdf import Rig


def test_step_keys_include_document_version_step_and_pipeline_version() -> None:
    from app.domain.pdf.document import Document

    doc = Document("d_9", "user:a", "t", "a" * 64, "k", version=3)
    assert StepLedger.key(doc, "scan", "pdf-ingest@1.4.0") == "d_9:3:scan:pdf-ingest@1.4.0"


def test_a_completed_memoised_step_is_not_executed_again() -> None:
    from app.domain.pdf.document import Document

    from tests.fakes.pdf import InMemoryDocuments

    repo = InMemoryDocuments()
    ledger = StepLedger(repo, "v1")
    doc = Document("d_1", "user:a", "t", "b" * 64, "k")
    calls: list[int] = []
    first = ledger.run(doc, "inspect", lambda: calls.append(1) or {"pages": 3})
    second = ledger.run(doc, "inspect", lambda: calls.append(1) or {"pages": 99})
    assert first == second == {"pages": 3} and calls == [1]


def test_a_failed_step_is_retried_and_only_then_recorded() -> None:
    from app.domain.pdf.document import Document

    from tests.fakes.pdf import InMemoryDocuments

    repo = InMemoryDocuments()
    ledger = StepLedger(repo, "v1")
    doc = Document("d_1", "user:a", "t", "b" * 64, "k")

    def boom() -> dict:
        raise StorageError("blip")

    with pytest.raises(StorageError):
        ledger.run(doc, "scan", boom)
    assert repo.steps() == []
    assert ledger.run(doc, "scan", lambda: {"clean": True}) == {"clean": True}


def test_a_new_pipeline_version_redoes_the_work() -> None:
    from app.domain.pdf.document import Document

    from tests.fakes.pdf import InMemoryDocuments

    repo, doc = InMemoryDocuments(), Document("d_1", "user:a", "t", "b" * 64, "k")
    calls: list[int] = []
    StepLedger(repo, "v1").run(doc, "inspect", lambda: calls.append(1) or {})
    StepLedger(repo, "v2").run(doc, "inspect", lambda: calls.append(1) or {})
    assert calls == [1, 1]


def test_a_retry_after_a_crash_skips_finished_steps_and_creates_no_duplicate_chunks() -> None:
    rig = Rig(indexer=FakeIndexer(fail_times=1))
    with pytest.raises(RuntimeError):
        rig.use_case.execute("d_1")
    scans, inspections = rig.scanner.scans, rig.inspector.calls
    rig.use_case.execute("d_1")
    assert (rig.scanner.scans, rig.inspector.calls) == (scans, inspections)  # resumed, not redone
    assert len(rig.indexer.chunks) == 3  # deterministic ids: upserted, not duplicated
    rig.use_case.execute("d_1")
    assert len(rig.indexer.chunks) == 3


@pytest.mark.parametrize(
    ("error", "transient"),
    [
        (ScannerUnavailableError("x"), True),
        (StorageError("x"), True),
        (TransientError("x"), True),
        (ConnectionError("x"), True),
        (TimeoutError("x"), True),
        (NotAPdfError(), False),
        (MalwareFoundError("x"), False),
        (ValueError("x"), False),
    ],
)
def test_only_transient_errors_are_retried(error: Exception, transient: bool) -> None:
    assert is_transient(error) is transient


def test_backoff_grows_exponentially_with_a_cap() -> None:
    assert [backoff_seconds(n, base=2, cap=60) for n in (0, 1, 2, 3, 10)] == [2, 4, 8, 16, 60]


def test_repeated_transient_failures_end_in_the_dead_letter_queue() -> None:
    from app.application.pdf.services.retry_policy import run_with_retries

    rig = Rig(scanner=FakeScanner(down=True))
    sleeps: list[float] = []
    outcome = run_with_retries(
        lambda: rig.use_case.execute("d_1"), "d_1", rig.repo, max_attempts=3, sleep=sleeps.append
    )
    assert outcome == "dead_lettered" and len(sleeps) == 2
    assert rig.repo.dead_letters == [("d_1", "ScannerUnavailableError", 3)]


def test_permanent_errors_are_not_retried_and_not_dead_lettered() -> None:
    from app.application.pdf.services.retry_policy import run_with_retries

    from tests.pdf_fixtures import EICAR, build_pdf

    rig = Rig(build_pdf() + EICAR)
    sleeps: list[float] = []
    outcome = run_with_retries(
        lambda: rig.use_case.execute("d_1"), "d_1", rig.repo, max_attempts=3, sleep=sleeps.append
    )
    assert outcome == "failed" and sleeps == [] and rig.repo.dead_letters == []


def test_success_after_a_transient_blip() -> None:
    from app.application.pdf.services.retry_policy import run_with_retries

    rig = Rig(indexer=FakeIndexer(fail_times=1, fail_with=StorageError("blip")))
    outcome = run_with_retries(
        lambda: rig.use_case.execute("d_1"), "d_1", rig.repo, max_attempts=3, sleep=lambda s: None
    )
    assert outcome == "ok" and rig.repo.get("d_1").status.value == "ready"  # type: ignore[union-attr]
