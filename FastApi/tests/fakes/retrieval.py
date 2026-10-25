import hashlib
import math
import re
from collections.abc import Sequence

from app.application.ports.embedder import Embedder
from app.application.ports.reranker import Reranker
from app.application.ports.vector_store import VectorSearcher, VectorWriter
from app.domain.entities import KnowledgeChunk
from app.domain.retrieval import IndexedChunk, ScoredChunk, SearchFilters
from app.domain.value_objects import Embedding

DIM = 128


def tokenize(text: str) -> list[str]:
    out: list[str] = []
    for word in re.findall(r"[A-Za-z0-9]+", text):
        parts = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", word)
        out.append(word.lower())
        if len(parts) > 1:
            out.extend(p.lower() for p in parts)
    return out


class FakeEmbedder(Embedder):
    """Deterministic hashed bag-of-words embedder: similar wording gives similar vectors."""

    version = "fake-hash-v1"
    dimension = DIM

    def __init__(self) -> None:
        self.calls = 0

    def embed(self, text: str) -> Embedding:
        self.calls += 1
        vec = [0.0] * DIM
        for token in tokenize(text):
            digest = hashlib.md5(token.encode(), usedforsecurity=False).digest()
            vec[int.from_bytes(digest[:4], "big") % DIM] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return Embedding(tuple(v / norm for v in vec))


def _matches(chunk: KnowledgeChunk, filters: SearchFilters) -> bool:
    return (
        (filters.language is None or chunk.language == filters.language)
        and (filters.framework is None or chunk.framework == filters.framework)
        and (filters.artifact_type is None or chunk.artifact_type == filters.artifact_type)
    )


class InMemoryVectorStore(VectorWriter, VectorSearcher):
    def __init__(self) -> None:
        self._items: dict[str, IndexedChunk] = {}

    def upsert(self, chunks: Sequence[IndexedChunk]) -> None:
        for item in chunks:
            self._items[item.chunk.id] = item

    def search(
        self, query_text: str, embedding: Embedding, filters: SearchFilters, top_k: int
    ) -> list[ScoredChunk]:
        scored = [
            ScoredChunk(
                i.chunk,
                sum(a * b for a, b in zip(embedding.values, i.embedding.values, strict=True)),
            )
            for i in self._items.values()
            if _matches(i.chunk, filters)
        ]
        return sorted(scored, key=lambda s: (-s.score, s.chunk.id))[:top_k]

    def __len__(self) -> int:
        return len(self._items)


class ReverseReranker(Reranker):
    """Test double proving the use case honours the reranker's order."""

    def rerank(self, query_text: str, hits: Sequence[ScoredChunk], top_k: int) -> list[ScoredChunk]:
        return list(reversed(hits))[:top_k]
