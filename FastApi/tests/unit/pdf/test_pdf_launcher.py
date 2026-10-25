import pytest
from app.adapters.outbound.pdf.celery_launcher import CeleryPipelineLauncher
from app.application.errors import QueueUnavailableError
from app.workers.pdf_tasks import make_pdf_tasks
from celery import Celery

from tests.unit.pdf.test_ingest_pdf import Rig


def test_launch_enqueues_on_the_ingest_queue() -> None:
    sent: list[dict] = []

    class Task:
        def apply_async(self, args, queue):  # type: ignore[no-untyped-def]
            sent.append({"args": args, "queue": queue})

    CeleryPipelineLauncher(Task()).launch("d_7")
    assert sent == [{"args": ["d_7"], "queue": "ingest"}]


def test_a_broker_outage_becomes_a_transient_queue_error() -> None:
    class Down:
        def apply_async(self, args, queue):  # type: ignore[no-untyped-def]
            raise ConnectionError("broker down")

    with pytest.raises(QueueUnavailableError):
        CeleryPipelineLauncher(Down()).launch("d_7")


def test_end_to_end_through_a_real_celery_app_in_eager_mode() -> None:
    rig = Rig()
    app = Celery("t", broker="memory://", backend="cache+memory://")
    app.conf.task_always_eager = True
    task = make_pdf_tasks(app, lambda: (rig.use_case, rig.repo), max_retries=3)
    CeleryPipelineLauncher(task).launch("d_1")
    assert rig.repo.get("d_1").status.value == "ready"  # type: ignore[union-attr]
