from __future__ import annotations

import re
import uuid
import zlib
from collections import Counter
from collections.abc import Sequence
from typing import Any

from qdrant_client import QdrantClient, models

from app.adapters.outbound.qdrant.bootstrap import DENSE, SPARSE, ensure_collection
from app.application.ports.vector_store import VectorSearcher, VectorWriter
from app.domain.entities import KnowledgeChunk
from app.domain.retrieval import IndexedChunk, ScoredChunk, SearchFilters
from app.domain.value_objects import Embedding

_TOKEN = re.compile(r"[A-Za-z0-9_@.]+")
_NAMESPACE = uuid.UUID("6f1d2c1e-6a4b-4b1a-9a53-2f7f3b1c9d10")
CANDIDATES = 50


_CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


def _tokens(text: str) -> list[str]:
    """Whole identifiers plus camelCase parts: `RestController` also matches "rest controller"."""
    out: list[str] = []
    for raw in _TOKEN.findall(text):
        word = raw.strip("@.")
        parts = _CAMEL.findall(word)
        out.append(word.lower())
        if len(parts) > 1:
            out.extend(p.lower() for p in parts)
    return out


def sparse_vector(text: str) -> models.SparseVector:
    """Term-frequency sparse vector; the collection's IDF modifier makes it BM25-style."""
    counts = Counter(zlib.crc32(t.encode()) for t in _tokens(text))
    indices = sorted(counts)
    return models.SparseVector(indices=indices, values=[float(counts[i]) for i in indices])


def point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, chunk_id))


def _filter(filters: SearchFilters) -> models.Filter | None:
    conditions = [
        models.FieldCondition(key=key, match=models.MatchValue(value=value))
        for key, value in (
            ("language", filters.language),
            ("framework", filters.framework),
            ("artifact_type", filters.artifact_type),
        )
        if value is not None
    ]
    return models.Filter(must=conditions) if conditions else None


class QdrantVectorStore(VectorWriter, VectorSearcher):
    """Hybrid dense + keyword search fused with Reciprocal Rank Fusion inside Qdrant."""

    def __init__(self, client: QdrantClient, collection: str, dimension: int) -> None:
        self._client = client
        self._collection = collection
        ensure_collection(client, collection, dimension)

    def upsert(self, chunks: Sequence[IndexedChunk]) -> None:
        points = [
            models.PointStruct(
                id=point_id(c.chunk.id),
                vector={DENSE: list(c.embedding.values), SPARSE: sparse_vector(c.chunk.text)},
                payload={
                    "chunk_id": c.chunk.id,
                    "text": c.chunk.text,
                    "language": c.chunk.language,
                    "framework": c.chunk.framework,
                    "artifact_type": c.chunk.artifact_type,
                    "source_url": c.chunk.source_url,
                },
            )
            for c in chunks
        ]
        if points:
            self._client.upsert(self._collection, points=points, wait=True)

    def search(
        self, query_text: str, embedding: Embedding, filters: SearchFilters, top_k: int
    ) -> list[ScoredChunk]:
        flt = _filter(filters)
        result = self._client.query_points(
            self._collection,
            prefetch=[
                models.Prefetch(
                    query=list(embedding.values), using=DENSE, limit=CANDIDATES, filter=flt
                ),
                models.Prefetch(
                    query=sparse_vector(query_text), using=SPARSE, limit=CANDIDATES, filter=flt
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            query_filter=flt,
            limit=top_k,
            with_payload=True,
        )
        hits = [self._to_scored(p.payload or {}, p.score) for p in result.points]
        return sorted(hits, key=lambda h: (-h.score, h.chunk.id))

    @staticmethod
    def _to_scored(payload: dict[str, Any], score: float) -> ScoredChunk:
        return ScoredChunk(
            KnowledgeChunk(
                id=payload["chunk_id"],
                text=payload["text"],
                language=payload["language"],
                framework=payload.get("framework"),
                artifact_type=payload.get("artifact_type"),
                source_url=payload.get("source_url"),
            ),
            score,
        )
