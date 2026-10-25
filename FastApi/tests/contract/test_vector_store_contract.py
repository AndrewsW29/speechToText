"""Contract every VectorWriter/VectorSearcher adapter must satisfy (Liskov)."""

from collections.abc import Callable
from typing import Any

import pytest
from app.application.ports.vector_store import VectorSearcher, VectorWriter
from app.domain.entities import KnowledgeChunk
from app.domain.retrieval import IndexedChunk, SearchFilters

from tests.fakes import FakeEmbedder, InMemoryVectorStore

EMBEDDER = FakeEmbedder()


def _in_memory() -> Any:
    return InMemoryVectorStore()


def _qdrant_local() -> Any:
    from app.adapters.outbound.qdrant.qdrant_vector_store import QdrantVectorStore
    from qdrant_client import QdrantClient

    return QdrantVectorStore(QdrantClient(":memory:"), "contract_test", EMBEDDER.dimension)


FACTORIES: dict[str, Callable[[], Any]] = {"in-memory": _in_memory, "qdrant-local": _qdrant_local}


@pytest.fixture(params=list(FACTORIES), ids=list(FACTORIES))
def store(request: pytest.FixtureRequest) -> Any:
    return FACTORIES[request.param]()


def _indexed(
    cid: str, text: str, language: str = "java", framework: str | None = "spring"
) -> IndexedChunk:
    chunk = KnowledgeChunk(id=cid, text=text, language=language, framework=framework)
    return IndexedChunk(chunk, EMBEDDER.embed(text))


CORPUS = [
    _indexed("c1", "create a rest controller with the RestController annotation"),
    _indexed("c2", "a service class holds business logic annotated with Service"),
    _indexed("c3", "dependency injection wires beans through the constructor"),
    _indexed(
        "k1", "kotlin coroutines launch structured concurrency", language="kotlin", framework=None
    ),
]


def _search(store: VectorSearcher, text: str, filters: SearchFilters | None = None, k: int = 5):  # type: ignore[no-untyped-def]
    return store.search(text, EMBEDDER.embed(text), filters or SearchFilters(), k)


def test_implements_both_ports(store: Any) -> None:
    assert isinstance(store, VectorWriter) and isinstance(store, VectorSearcher)


def test_results_are_sorted_by_score_descending(store: Any) -> None:
    store.upsert(CORPUS)
    scores = [h.score for h in _search(store, "rest controller annotation")]
    assert scores == sorted(scores, reverse=True) and len(scores) >= 2


def test_most_relevant_chunk_is_first(store: Any) -> None:
    store.upsert(CORPUS)
    assert _search(store, "how do I create a rest controller")[0].chunk.id == "c1"


def test_respects_top_k(store: Any) -> None:
    store.upsert(CORPUS)
    assert len(_search(store, "controller service injection", k=2)) == 2


def test_upsert_is_idempotent(store: Any) -> None:
    store.upsert(CORPUS)
    store.upsert(CORPUS)
    ids = [h.chunk.id for h in _search(store, "controller service injection coroutines", k=10)]
    assert sorted(ids) == sorted(set(ids)) and len(ids) == len(CORPUS)


def test_filters_by_language(store: Any) -> None:
    store.upsert(CORPUS)
    hits = _search(store, "concurrency coroutines controller", SearchFilters(language="kotlin"))
    assert {h.chunk.language for h in hits} == {"kotlin"}


def test_filters_by_framework_and_returns_empty_when_nothing_matches(store: Any) -> None:
    store.upsert(CORPUS)
    assert _search(store, "anything", SearchFilters(language="java", framework="quarkus")) == []


def test_upsert_replaces_existing_chunk(store: Any) -> None:
    store.upsert(CORPUS)
    store.upsert([_indexed("c1", "completely new content about repositories and JPA")])
    top = _search(store, "completely new content repositories JPA")[0]
    assert top.chunk.id == "c1" and "repositories" in top.chunk.text
