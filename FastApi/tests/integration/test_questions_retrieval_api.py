from app.adapters.outbound.answer.top_chunks_answer_generator import TopChunksAnswerGenerator
from app.adapters.outbound.rerank.score_reranker import ScoreReranker
from app.application.services.retriever import Retriever
from app.application.use_cases.ask_question import AskQuestion
from app.config import Settings
from app.domain.entities import KnowledgeChunk
from app.domain.retrieval import IndexedChunk
from app.main import Container, create_app
from fastapi.testclient import TestClient

from tests.fakes import FakeEmbedder, FakeTranscriber, InMemoryVectorStore
from tests.integration.conftest import WEBM


def _client(question: str) -> TestClient:
    embedder, store = FakeEmbedder(), InMemoryVectorStore()
    text = "A RestController exposes the service over HTTP"
    store.upsert(
        [
            IndexedChunk(
                KnowledgeChunk(
                    "c1",
                    text,
                    "java",
                    "spring",
                    source_url="https://docs.spring.io/x/mvc-controller",
                ),
                embedder.embed(text),
            )
        ]
    )
    uc = AskQuestion(
        FakeTranscriber(question),
        TopChunksAnswerGenerator(),
        Retriever(embedder, store, ScoreReranker()),
    )
    return TestClient(
        create_app(Settings(auth_enabled=False), container=Container(ask_question=uc))
    )


def test_answer_is_grounded_in_retrieved_sources() -> None:
    r = _client("how do I create a rest controller in java").post(
        "/v1/questions", files={"audio": ("q.webm", WEBM, "audio/webm")}
    )
    body = r.json()
    assert r.status_code == 200 and "RestController" in body["answer"]["text"]
    assert body["answer"]["sources"][0] == {
        "id": "c1",
        "title": "docs.spring.io: mvc controller",
        "kind": "documentation",
        "url": "https://docs.spring.io/x/mvc-controller",
    }


def test_question_without_knowledge_is_404_problem_not_a_made_up_answer() -> None:
    r = _client("explain swift actors").post(
        "/v1/questions", files={"audio": ("q.webm", WEBM, "audio/webm")}
    )
    assert r.status_code == 404 and r.headers["content-type"].startswith("application/problem+json")
