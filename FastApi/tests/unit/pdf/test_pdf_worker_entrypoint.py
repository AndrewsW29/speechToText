def test_the_worker_entrypoint_registers_the_pdf_task_and_the_queue_routes() -> None:
    from app.workers.pdf_worker import TASK_NAME, celery_app

    assert TASK_NAME in celery_app.tasks
    routes = celery_app.conf.task_routes
    assert routes["pdf.ingest"] == {"queue": "ingest"} and routes["pdf.ocr"] == {"queue": "gpu"}
