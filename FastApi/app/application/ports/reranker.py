from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.retrieval import ScoredChunk


class Reranker(ABC):
    @abstractmethod
    def rerank(self, query_text: str, hits: Sequence[ScoredChunk], top_k: int) -> list[ScoredChunk]:
        """Reorder candidates; result is sorted by score descending and truncated to top_k."""
