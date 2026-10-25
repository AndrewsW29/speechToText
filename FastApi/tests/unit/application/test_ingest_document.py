import pytest
from app.application.ports.document_source import DocumentSource
from app.application.services.chunking import SentenceChunker
from app.application.use_cases.ingest_document import IngestDocument, IngestionFacade
from app.domain.retrieval import Document, SearchFilters, chunk_id

from tests.fakes import FakeEmbedder, InMemoryVectorStore

DOC = Document(
    source_url="https://docs.example/spring/rest",
    text="A RestController exposes endpoints. A Service holds the business logic.",
    language="java",
    framework="spring",
)


def _use_case() -> tuple[IngestDocument, InMemoryVectorStore, FakeEmbedder]:
    store, embedder = InMemoryVectorStore(), FakeEmbedder()
    return IngestDocument(embedder, store, SentenceChunker(max_chars=45)), store, embedder


def test_ingests_chunks_with_metadata() -> None:
    uc, store, embedder = _use_case()
    result = uc.execute(DOC)
    assert result.chunks == len(store) >= 2
    hit = store.search("business logic", embedder.embed("business logic"), SearchFilters(), 1)[0]
    assert hit.chunk.language == "java" and hit.chunk.framework == "spring"
    assert hit.chunk.source_url == DOC.source_url


def test_ingesting_the_same_document_twice_creates_no_duplicates() -> None:
    uc, store, _ = _use_case()
    first = uc.execute(DOC)
    second = uc.execute(DOC)
    assert len(store) == first.chunks == second.chunks


def test_chunk_ids_are_content_hashes() -> None:
    assert chunk_id("u", "same  text") == chunk_id("u", "same text")
    assert chunk_id("u", "a") != chunk_id("u", "b")
    assert chunk_id("u1", "a") != chunk_id("u2", "a")


def test_changed_content_gets_a_new_id() -> None:
    uc, store, _ = _use_case()
    uc.execute(DOC)
    before = len(store)
    uc.execute(Document(DOC.source_url, DOC.text + " Extra sentence here.", "java", "spring"))
    assert len(store) > before


def test_empty_document_ingests_nothing() -> None:
    uc, store, _ = _use_case()
    assert uc.execute(Document("u", "   ", "java")).chunks == 0 and len(store) == 0


class FakeSource(DocumentSource):
    def fetch(
        self, url: str, language: str = "java", framework: str | None = None
    ) -> list[Document]:
        return [
            DOC,
            Document(url + "/two", "Validation uses annotations on the DTO.", "java", "spring"),
        ]


def test_facade_fetches_and_ingests_everything() -> None:
    uc, store, _ = _use_case()
    summary = IngestionFacade(FakeSource(), uc).ingest("https://docs.example/spring")
    assert summary.documents == 2 and summary.chunks == len(store)


def test_facade_rejects_blank_url() -> None:
    uc, _, _ = _use_case()
    with pytest.raises(ValueError):
        IngestionFacade(FakeSource(), uc).ingest(" ")
