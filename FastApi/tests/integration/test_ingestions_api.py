from pathlib import Path

import pytest
from app.adapters.outbound.answer.fixed_answer_generator import FixedAnswerGenerator
from app.adapters.outbound.ingestion.document_sources import LocalDirectorySource
from app.adapters.outbound.ingestion.inline_jobs import InlineIngestionJobs
from app.application.services.chunking import CodeAwareChunker, SentenceChunker
from app.application.use_cases.ask_question import AskQuestion
from app.application.use_cases.ingest_document import IngestDocument, IngestionFacade
from app.config import Settings
from app.main import Container, create_app
from fastapi.testclient import TestClient

from tests.fakes import FakeEmbedder, FakeTranscriber, InMemoryVectorStore


@pytest.fixture
def docs(tmp_path: Path) -> Path:
    (tmp_path / "a.md").write_text(
        "---\nsource_url: https://docs.example/a\nlanguage: java\nframework: spring\n---\n"
        "A Service holds business logic. A RestController exposes it."
    )
    return tmp_path


@pytest.fixture
def client(docs: Path) -> tuple[TestClient, InMemoryVectorStore]:
    store = InMemoryVectorStore()
    ingest = IngestDocument(FakeEmbedder(), store, SentenceChunker(60), CodeAwareChunker())
    jobs = InlineIngestionJobs(IngestionFacade(LocalDirectorySource(), ingest))
    container = Container(
        ask_question=AskQuestion(FakeTranscriber(), FixedAnswerGenerator()), ingestion=jobs
    )
    app = create_app(Settings(auth_enabled=False), container=container)
    return TestClient(app), store


def test_submit_returns_202_and_job_completes(client, docs) -> None:  # type: ignore[no-untyped-def]
    api, store = client
    response = api.post("/v1/ingestions", json={"url": str(docs)})
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    status = api.get(f"/v1/ingestions/{job_id}").json()
    assert (
        status["state"] == "succeeded"
        and status["documents"] == 1
        and status["chunks"] == len(store) > 0
    )


def test_resubmitting_does_not_duplicate_chunks(client, docs) -> None:  # type: ignore[no-untyped-def]
    api, store = client
    api.post("/v1/ingestions", json={"url": str(docs)})
    before = len(store)
    api.post("/v1/ingestions", json={"url": str(docs)})
    assert len(store) == before


def test_failed_job_reports_failure_without_internals(client) -> None:  # type: ignore[no-untyped-def]
    api, _ = client
    job_id = api.post("/v1/ingestions", json={"url": "/definitely/not/here"}).json()["job_id"]
    status = api.get(f"/v1/ingestions/{job_id}").json()
    assert status["state"] == "failed" and "Traceback" not in str(status)


def test_unknown_job_is_404_problem(client) -> None:  # type: ignore[no-untyped-def]
    api, _ = client
    response = api.get("/v1/ingestions/nope")
    assert response.status_code == 404 and response.headers["content-type"].startswith(
        "application/problem+json"
    )


def test_blank_url_is_422(client) -> None:  # type: ignore[no-untyped-def]
    api, _ = client
    assert api.post("/v1/ingestions", json={"url": " "}).status_code == 422
