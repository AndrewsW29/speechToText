from app.adapters.outbound.ingestion.celery_jobs import CeleryIngestionJobs
from app.application.use_cases.ingest_document import IngestSummary
from app.workers.ingestion_tasks import make_ingestion_task
from celery import Celery


class StubFacade:
    def __init__(self, fail: bool = False) -> None:
        self.fail, self.calls = fail, []

    def ingest(
        self, url: str, language: str = "java", framework: str | None = None
    ) -> IngestSummary:
        self.calls.append((url, language, framework))
        if self.fail:
            raise RuntimeError("boom with secret internals")
        return IngestSummary(documents=2, chunks=7)


def _jobs(facade: StubFacade) -> CeleryIngestionJobs:
    app = Celery("t", broker="memory://", backend="cache+memory://")
    app.conf.task_always_eager = True
    app.conf.task_store_eager_result = True
    task = make_ingestion_task(app, lambda: facade)  # type: ignore[arg-type]
    return CeleryIngestionJobs(task, app)


def test_submit_runs_the_task_and_status_reports_success() -> None:
    facade = StubFacade()
    jobs = _jobs(facade)
    job_id = jobs.submit("https://docs.example", "java", "spring")
    status = jobs.status(job_id)
    assert status is not None and status.state == "succeeded"
    assert (status.documents, status.chunks) == (2, 7)
    assert facade.calls == [("https://docs.example", "java", "spring")]


def test_failure_is_reported_without_internals() -> None:
    jobs = _jobs(StubFacade(fail=True))
    status = jobs.status(jobs.submit("u", "java", None))
    assert status is not None and status.state == "failed"
    assert status.error == "ingestion failed" and "secret" not in str(status)


def test_unknown_job_is_pending_and_reported_as_queued() -> None:
    jobs = _jobs(StubFacade())
    status = jobs.status("00000000-unknown")
    assert status is not None and status.state == "queued"


def test_worker_entrypoint_registers_the_ingestion_task() -> None:
    from app.workers.worker import TASK_NAME, celery_app

    assert TASK_NAME in celery_app.tasks
