import pytest
from app.adapters.outbound.postgres.database import create_engine
from app.config import Settings
from app.workers.celery_app import create_celery


def test_celery_uses_redis_url_from_settings() -> None:
    app = create_celery(Settings(redis_url="redis://cache:6379/1"))  # type: ignore[arg-type]
    assert app.conf.broker_url == "redis://cache:6379/1"
    assert app.conf.task_serializer == "json"


def test_engine_requires_database_url() -> None:
    with pytest.raises(RuntimeError):
        create_engine(Settings())


def test_engine_builds_from_secret_url() -> None:
    engine = create_engine(Settings(database_url="postgresql+asyncpg://u:p@localhost/db"))  # type: ignore[arg-type]
    assert engine.url.drivername == "postgresql+asyncpg"
