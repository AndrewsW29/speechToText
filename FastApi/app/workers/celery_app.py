from celery import Celery

from app.config import Settings, get_settings


def create_celery(settings: Settings | None = None) -> Celery:
    settings = settings or get_settings()
    url = (
        settings.redis_url.get_secret_value() if settings.redis_url else "redis://localhost:6379/0"
    )
    app = Celery("voice_assistant", broker=url, backend=url)
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        task_acks_late=True,
        task_time_limit=900,
        worker_prefetch_multiplier=1,
        timezone="UTC",
    )
    return app


celery_app = create_celery()
