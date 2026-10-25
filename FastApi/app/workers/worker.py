"""Celery worker entrypoint: `celery -A app.workers.worker worker`."""

from app.workers.celery_app import celery_app
from app.workers.ingestion_tasks import TASK_NAME, register_default_tasks

register_default_tasks()

__all__ = ["TASK_NAME", "celery_app"]
