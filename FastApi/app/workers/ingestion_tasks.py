from __future__ import annotations

from collections.abc import Callable
from typing import Any

from celery import Celery

from app.application.use_cases.ingest_document import IngestionFacade

TASK_NAME = "ingestion.run"


def make_ingestion_task(app: Celery, facade_factory: Callable[[], IngestionFacade]) -> Any:
    """Register the ingestion task on `app`; the facade is built lazily inside the worker."""

    @app.task(name=TASK_NAME)  # type: ignore[untyped-decorator]
    def run_ingestion(
        url: str, language: str = "java", framework: str | None = None
    ) -> dict[str, int]:
        summary = facade_factory().ingest(url, language, framework)
        return {"documents": summary.documents, "chunks": summary.chunks}

    return run_ingestion


def _default_facade() -> IngestionFacade:
    from app.bootstrap import build_ingestion_facade
    from app.config import get_settings

    return build_ingestion_facade(get_settings())


def register_default_tasks() -> Any:
    from app.workers.celery_app import celery_app

    return make_ingestion_task(celery_app, _default_facade)
