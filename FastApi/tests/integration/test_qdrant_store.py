"""Qdrant adapter against a real server in a container (skipped when Docker is unavailable)."""

import pytest

pytest.importorskip("testcontainers")

from app.adapters.outbound.qdrant.qdrant_vector_store import QdrantVectorStore
from app.domain.entities import KnowledgeChunk
from app.domain.retrieval import IndexedChunk, SearchFilters
from qdrant_client import QdrantClient
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from tests.fakes import FakeEmbedder

pytestmark = pytest.mark.integration
EMBEDDER = FakeEmbedder()


@pytest.fixture(scope="module")
def client():  # type: ignore[no-untyped-def]
    try:
        container = DockerContainer("qdrant/qdrant:latest").with_exposed_ports(6333)
        container.start()
    except Exception as exc:  # Docker not reachable
        pytest.skip(f"docker unavailable: {exc}")
    try:
        wait_for_logs(container, "Qdrant HTTP listening", timeout=60)
        yield QdrantClient(
            host=container.get_container_host_ip(), port=int(container.get_exposed_port(6333))
        )
    finally:
        container.stop()


def _row(i: str, text: str, language: str = "java") -> IndexedChunk:
    return IndexedChunk(
        KnowledgeChunk(i, text, language, "spring", source_url=f"https://d/{i}"),
        EMBEDDER.embed(text),
    )


def test_hybrid_search_with_payload_filters_on_a_real_server(client) -> None:  # type: ignore[no-untyped-def]
    store = QdrantVectorStore(client, "it_code_knowledge", EMBEDDER.dimension)
    store.upsert(
        [
            _row("c", "RestController exposes endpoints with GetMapping"),
            _row("s", "Service holds business logic"),
            _row("k", "coroutines launch scope", "kotlin"),
        ]
    )
    q = "create a rest controller"
    hits = store.search(q, EMBEDDER.embed(q), SearchFilters(language="java", framework="spring"), 5)
    assert hits[0].chunk.id == "c"
    assert {h.chunk.language for h in hits} == {"java"}
    assert [h.score for h in hits] == sorted((h.score for h in hits), reverse=True)
    store.upsert([_row("c", "RestController exposes endpoints with GetMapping")])
    assert len(store.search(q, EMBEDDER.embed(q), SearchFilters(), 10)) == 3  # idempotent
