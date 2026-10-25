"""Runs the pipeline in-process: for tests and local development without a Celery worker."""

from __future__ import annotations

import logging

from app.application.pdf.ports.pipeline_stages import PipelineLauncher
from app.application.pdf.use_cases.ingest_pdf import IngestPdf

logger = logging.getLogger(__name__)


class InlineLauncher(PipelineLauncher):
    def __init__(self, ingest: IngestPdf) -> None:
        self._ingest = ingest

    def launch(self, document_id: str) -> None:
        try:
            self._ingest.execute(document_id)
        except (
            Exception
        ) as exc:  # the document already carries the failure; the upload itself succeeded
            logger.warning("inline ingestion of %s failed: %s", document_id, type(exc).__name__)
