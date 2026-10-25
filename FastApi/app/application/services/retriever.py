from __future__ import annotations

from app.application.ports.embedder import Embedder
from app.application.ports.reranker import Reranker
from app.application.ports.vector_store import VectorSearcher
from app.domain.retrieval import ScoredChunk, SearchFilters, extract_filters

OVERFETCH = 4
MIN_CANDIDATES = 20


class Retriever:
    """embed -> filtered hybrid search -> rerank. Depends only on ports."""

    def __init__(
        self, embedder: Embedder, searcher: VectorSearcher, reranker: Reranker, top_k: int = 5
    ) -> None:
        self._embedder = embedder
        self._searcher = searcher
        self._reranker = reranker
        self._top_k = top_k

    def retrieve(self, question: str, filters: SearchFilters | None = None) -> list[ScoredChunk]:
        """`filters` come from the intent model's entities; otherwise use keyword extraction."""
        embedding = self._embedder.embed(question)
        candidates = self._searcher.search(
            question,
            embedding,
            filters if filters is not None else extract_filters(question),
            max(self._top_k * OVERFETCH, MIN_CANDIDATES),
        )
        return self._reranker.rerank(question, candidates, self._top_k)
