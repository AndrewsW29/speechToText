"""Composition helpers shared by the API (app.main) and the Celery worker."""

from __future__ import annotations

from functools import lru_cache

from qdrant_client import QdrantClient

from app.adapters.outbound.cache.redis_cache import RedisCache
from app.adapters.outbound.embeddings.cached_embedder import CachedEmbedder
from app.adapters.outbound.embeddings.sentence_transformer_embedder import (
    SentenceTransformerEmbedder,
)
from app.adapters.outbound.ingestion.document_sources import (
    HttpDocumentSource,
    LocalDirectorySource,
)
from app.adapters.outbound.qdrant.qdrant_vector_store import QdrantVectorStore
from app.adapters.outbound.rerank.score_reranker import ScoreReranker
from app.application.ports.document_source import DocumentSource
from app.application.ports.embedder import Embedder
from app.application.services.chunking import CodeAwareChunker, SentenceChunker
from app.application.services.retriever import Retriever
from app.application.use_cases.ingest_document import IngestDocument, IngestionFacade
from app.config import Settings
from app.domain.retrieval import Document


class RoutingDocumentSource(DocumentSource):
    """Local directories for trusted seeding, allowlisted HTTP(S) for everything else."""

    def __init__(self, http: HttpDocumentSource, local: LocalDirectorySource | None = None) -> None:
        self._http = http
        self._local = local

    def fetch(
        self, url: str, language: str = "java", framework: str | None = None
    ) -> list[Document]:
        if url.startswith(("http://", "https://")):
            return self._http.fetch(url, language, framework)
        if self._local is None:
            from app.adapters.outbound.ingestion.document_sources import UrlNotAllowedError

            raise UrlNotAllowedError("only http(s) URLs can be ingested")
        return self._local.fetch(url, language, framework)


@lru_cache
def _qdrant(url: str) -> QdrantClient:
    return QdrantClient(location=url) if url == ":memory:" else QdrantClient(url=url)


def build_embedder(settings: Settings) -> Embedder:
    embedder: Embedder = SentenceTransformerEmbedder(
        settings.embedding_model, settings.embedding_dimension
    )
    if settings.redis_url is not None:
        from redis import Redis

        embedder = CachedEmbedder(
            embedder, RedisCache(Redis.from_url(settings.redis_url.get_secret_value()))
        )
    return embedder


def build_vector_store(settings: Settings, embedder: Embedder) -> QdrantVectorStore:
    if settings.qdrant_url is None:
        raise RuntimeError("VA_QDRANT_URL is not set")
    return QdrantVectorStore(
        _qdrant(settings.qdrant_url), settings.qdrant_collection, embedder.dimension
    )


def build_retriever(settings: Settings) -> Retriever:
    embedder = build_embedder(settings)
    return Retriever(
        embedder, build_vector_store(settings, embedder), ScoreReranker(), settings.retrieval_top_k
    )


def build_ingestion_facade(settings: Settings, *, allow_local: bool = False) -> IngestionFacade:
    embedder = build_embedder(settings)
    ingest = IngestDocument(
        embedder, build_vector_store(settings, embedder), SentenceChunker(), CodeAwareChunker()
    )
    source = RoutingDocumentSource(
        HttpDocumentSource(settings.ingest_allowed_hosts),
        LocalDirectorySource() if allow_local else None,
    )
    return IngestionFacade(source, ingest)
