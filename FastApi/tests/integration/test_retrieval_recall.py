"""recall@5 over the known-question set against the seed corpus (hybrid search, local Qdrant)."""

import json
from pathlib import Path

import pytest
from app.adapters.outbound.ingestion.document_sources import LocalDirectorySource
from app.adapters.outbound.qdrant.qdrant_vector_store import QdrantVectorStore
from app.adapters.outbound.rerank.score_reranker import ScoreReranker
from app.application.services.chunking import CodeAwareChunker, SentenceChunker
from app.application.services.retriever import Retriever
from app.application.use_cases.ingest_document import IngestDocument, IngestionFacade
from qdrant_client import QdrantClient

from tests.fakes import FakeEmbedder

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "ml" / "training" / "seed_corpus"
QUESTIONS = json.loads((ROOT / "tests" / "data" / "retrieval_questions.json").read_text())
RECALL_AT = 5
GATE = 0.85


@pytest.fixture(scope="module")
def retriever() -> Retriever:
    embedder = FakeEmbedder()
    store = QdrantVectorStore(QdrantClient(":memory:"), "recall_test", embedder.dimension)
    facade = IngestionFacade(
        LocalDirectorySource(),
        IngestDocument(embedder, store, SentenceChunker(400), CodeAwareChunker()),
    )
    summary = facade.ingest(str(CORPUS))
    assert summary.documents == 9 and summary.chunks >= 9
    return Retriever(embedder, store, ScoreReranker(), top_k=RECALL_AT)


def test_recall_at_5_meets_the_gate(retriever: Retriever) -> None:
    hits = 0
    misses = []
    for item in QUESTIONS:
        urls = [h.chunk.source_url for h in retriever.retrieve(item["q"])]
        if item["expect"] in urls:
            hits += 1
        else:
            misses.append(item["q"])
    recall = hits / len(QUESTIONS)
    assert recall >= GATE, f"recall@{RECALL_AT}={recall:.2f} < {GATE}; misses={misses}"


def test_java_question_never_returns_kotlin_chunks(retriever: Retriever) -> None:
    assert {
        h.chunk.language for h in retriever.retrieve("how do I create a controller in Java")
    } == {"java"}


def test_controller_and_service_question_returns_both_artifacts(retriever: Retriever) -> None:
    text = " ".join(
        h.chunk.text for h in retriever.retrieve("create a controller and a service in Java")
    )
    assert "RestController" in text and "Service" in text
