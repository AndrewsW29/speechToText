"""The Alembic migration and the SQL repository against a real PostgreSQL (skipped without Docker)."""

import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

pytest.importorskip("testcontainers")
from app.adapters.outbound.postgres.document_repository import SqlDocumentRepository
from app.domain.pdf.document import Document, DocumentStatus
from testcontainers.postgres import PostgresContainer

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def postgres():  # type: ignore[no-untyped-def]
    try:
        container = PostgresContainer("postgres:17-alpine", driver=None)
        container.start()
    except Exception as exc:
        pytest.skip(f"docker unavailable: {exc}")
    try:
        yield container
    finally:
        container.stop()


def test_migration_creates_the_schema_and_the_repository_works_on_it(postgres) -> None:  # type: ignore[no-untyped-def]
    host, port = postgres.get_container_host_ip(), postgres.get_exposed_port(5432)
    creds = f"{postgres.username}:{postgres.password}@{host}:{port}/{postgres.dbname}"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={
            "VA_DATABASE_URL": f"postgresql+asyncpg://{creds}",
            "PATH": "/usr/bin:/bin",
            "HOME": str(Path.home()),
        },
    )
    assert result.returncode == 0, result.stderr[-2000:]

    engine = create_engine(f"postgresql+psycopg://{creds}")
    assert {"documents", "document_versions", "ingest_steps", "dead_letters"} <= set(
        inspect(engine).get_table_names()
    )

    repo = SqlDocumentRepository(engine)
    doc = Document("d_pg1", "user:a", "guide.pdf", "a" * 64, "sha256/aa/a", size_bytes=10)
    repo.add(doc)
    repo.save(doc.with_status(DocumentStatus.READY).with_pages(3).with_flags("javascript"))
    got = repo.get("d_pg1")
    assert got is not None and got.status is DocumentStatus.READY and got.flags == ("javascript",)
    assert repo.find_by_hash("user:a", "a" * 64).id == "d_pg1"  # type: ignore[union-attr]
    with pytest.raises(Exception, match=r"uq_documents_owner_sha256|unique"):
        repo.add(Document("d_pg2", "user:a", "again.pdf", "a" * 64, "k"))
    repo.put_step("d_pg1:1:scan:v", "d_pg1", {"clean": True})
    assert repo.get_step("d_pg1:1:scan:v") == {"clean": True}
