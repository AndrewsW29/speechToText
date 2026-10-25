"""Resumable pipeline steps: finished steps are recorded by (doc, version, step, pipeline)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.application.pdf.ports.document_repository import StepStore
from app.domain.pdf.document import Document


class StepLedger:
    def __init__(self, store: StepStore, pipeline_version: str) -> None:
        self._store = store
        self._pipeline_version = pipeline_version

    @staticmethod
    def key(document: Document, step: str, pipeline_version: str) -> str:
        return f"{document.id}:{document.version}:{step}:{pipeline_version}"

    def run(
        self, document: Document, step: str, fn: Callable[[], dict[str, Any]]
    ) -> dict[str, Any]:
        """Run `fn` unless this exact step already finished for this pipeline version.

        Only successful results are recorded, so a failed step is retried from scratch.
        """
        key = self.key(document, step, self._pipeline_version)
        if (done := self._store.get_step(key)) is not None:
            return done
        result = fn()
        self._store.put_step(key, document.id, result)
        return result
