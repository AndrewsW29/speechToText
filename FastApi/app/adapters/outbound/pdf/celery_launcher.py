from __future__ import annotations

from typing import Any

from app.application.errors import QueueUnavailableError
from app.application.pdf.ports.pipeline_stages import PipelineLauncher


class CeleryPipelineLauncher(PipelineLauncher):
    def __init__(self, task: Any, queue: str = "ingest") -> None:
        self._task = task
        self._queue = queue

    def launch(self, document_id: str) -> None:
        try:
            self._task.apply_async(args=[document_id], queue=self._queue)
        except Exception as exc:
            raise QueueUnavailableError("could not enqueue the document") from exc
