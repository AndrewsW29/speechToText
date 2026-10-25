from app.application.errors import NotAPdfError
from app.workers.pdf_tasks import QUEUE_ROUTES, make_pdf_tasks, process_document
from celery import Celery

from tests.fakes.pdf import FakeIndexer, FakeScanner, InMemoryDocuments
from tests.unit.pdf.test_ingest_pdf import Rig


def test_success_is_reported_ok() -> None:
    rig = Rig()
    assert process_document(rig.use_case, rig.repo, "d_1", retries=0, max_retries=3) == ("ok", None)


def test_transient_errors_ask_for_a_retry_with_exponential_countdown() -> None:
    rig = Rig(scanner=FakeScanner(down=True))
    assert process_document(rig.use_case, rig.repo, "d_1", retries=0, max_retries=3)[0] == "retry"
    outcome, countdown = process_document(rig.use_case, rig.repo, "d_1", retries=2, max_retries=3)
    assert (outcome, countdown) == ("retry", 8.0)


def test_exhausted_retries_dead_letter_the_document() -> None:
    rig = Rig(scanner=FakeScanner(down=True))
    assert process_document(rig.use_case, rig.repo, "d_1", retries=3, max_retries=3) == (
        "dead_lettered",
        None,
    )
    assert rig.repo.dead_letters == [("d_1", "ScannerUnavailableError", 4)]


def test_permanent_errors_fail_without_retry() -> None:
    from tests.fakes.pdf import FakeInspector

    class Garbage(FakeInspector):
        def inspect(self, data):  # type: ignore[no-untyped-def]
            raise NotAPdfError

    rig = Rig(inspector=Garbage())
    assert process_document(rig.use_case, rig.repo, "d_1", retries=0, max_retries=3) == (
        "failed",
        None,
    )
    assert rig.repo.dead_letters == []


def test_a_document_that_vanished_is_not_retried_forever() -> None:
    rig = Rig()
    assert process_document(
        rig.use_case, InMemoryDocuments(), "d_ghost", retries=0, max_retries=3
    ) == ("failed", None)


def test_queues_isolate_cpu_gpu_and_low_priority_work() -> None:
    assert QUEUE_ROUTES["pdf.ingest"] == {"queue": "ingest"}
    assert QUEUE_ROUTES["pdf.ocr"] == {"queue": "gpu"}
    assert QUEUE_ROUTES["pdf.learn.*"] == {"queue": "learn"}


def test_the_registered_task_runs_the_pipeline_eagerly() -> None:
    rig = Rig(indexer=FakeIndexer())
    app = Celery("t", broker="memory://", backend="cache+memory://")
    app.conf.task_always_eager = True
    task = make_pdf_tasks(app, lambda: (rig.use_case, rig.repo), max_retries=3)
    assert task.apply(args=["d_1"]).get() == "ok"
    assert rig.repo.get("d_1").status.value == "ready"  # type: ignore[union-attr]
