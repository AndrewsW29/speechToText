from __future__ import annotations

from typing import Any

from celery import Celery
from celery.result import AsyncResult

from app.application.ports.ingestion_jobs import IngestionJobs, JobStatus

_STATES = {"PENDING": "queued", "RECEIVED": "queued", "STARTED": "running", "RETRY": "running"}


class CeleryIngestionJobs(IngestionJobs):
    """Runs ingestion on Celery workers; status comes from the result backend."""

    def __init__(self, task: Any, app: Celery) -> None:
        self._task = task
        self._app = app

    def submit(self, url: str, language: str, framework: str | None) -> str:
        return str(self._task.apply_async(args=[url, language, framework]).id)

    def status(self, job_id: str) -> JobStatus | None:
        result = AsyncResult(job_id, app=self._app)
        if result.state == "SUCCESS":
            data = result.result or {}
            return JobStatus(job_id, "succeeded", data.get("documents", 0), data.get("chunks", 0))
        if result.state == "FAILURE":
            return JobStatus(job_id, "failed", error="ingestion failed")
        return JobStatus(job_id, _STATES.get(result.state, "queued"))
