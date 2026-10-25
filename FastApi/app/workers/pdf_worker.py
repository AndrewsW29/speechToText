"""PDF worker entrypoint: `celery -A app.workers.pdf_worker worker -Q ingest`."""

from app.bootstrap_pdf import worker_pipeline
from app.config import get_settings
from app.workers.celery_app import celery_app
from app.workers.pdf_tasks import TASK_NAME, configure_queues, make_pdf_tasks

configure_queues(celery_app)
make_pdf_tasks(celery_app, lambda: worker_pipeline(get_settings()), get_settings().pdf_max_retries)

__all__ = ["TASK_NAME", "celery_app"]
