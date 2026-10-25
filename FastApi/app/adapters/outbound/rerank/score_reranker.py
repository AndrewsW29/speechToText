from collections.abc import Sequence

from app.application.ports.reranker import Reranker
from app.domain.retrieval import ScoredChunk


class ScoreReranker(Reranker):
    """Baseline reranker: keep the retriever's score, deterministic tie-break by id."""

    def rerank(self, query_text: str, hits: Sequence[ScoredChunk], top_k: int) -> list[ScoredChunk]:
        return sorted(hits, key=lambda h: (-h.score, h.chunk.id))[:top_k]
