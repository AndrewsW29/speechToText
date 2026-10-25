from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.retrieval import IndexedChunk, ScoredChunk, SearchFilters
from app.domain.value_objects import Embedding


class VectorWriter(ABC):
    """Ingestion needs only the write side (interface segregation)."""

    @abstractmethod
    def upsert(self, chunks: Sequence[IndexedChunk]) -> None:
        """Insert or replace chunks by id; repeating the call must not create duplicates."""


class VectorSearcher(ABC):
    """The query path needs only the search side."""

    @abstractmethod
    def search(
        self, query_text: str, embedding: Embedding, filters: SearchFilters, top_k: int
    ) -> list[ScoredChunk]:
        """Return at most top_k hits sorted by score, highest first."""
