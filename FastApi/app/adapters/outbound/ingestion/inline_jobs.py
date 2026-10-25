"""Synchronous in-process jobs for local development and tests."""

from __future__ import annotations

import logging
from uuid import uuid4

from app.application.ports.ingestion_jobs import IngestionJobs, JobStatus
from app.application.use_cases.ingest_document import IngestionFacade

logger = logging.getLogger(__name__)


class InlineIngestionJobs(IngestionJobs):
    def __init__(self, facade: IngestionFacade) -> None:
        self._facade = facade
        self._jobs: dict[str, JobStatus] = {}

    def submit(self, url: str, language: str, framework: str | None) -> str:
        job_id = uuid4().hex
        try:
            summary = self._facade.ingest(url, language, framework)
            self._jobs[job_id] = JobStatus(job_id, "succeeded", summary.documents, summary.chunks)
        except Exception as exc:
            logger.warning("ingestion job %s failed: %s", job_id, exc)
            self._jobs[job_id] = JobStatus(job_id, "failed", error="ingestion failed")
        return job_id

    def status(self, job_id: str) -> JobStatus | None:
        return self._jobs.get(job_id)
