from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.entities import Answer, Query
from app.domain.retrieval import ScoredChunk


class AnswerGenerator(ABC):
    """Outbound port: compose an answer for a query from retrieved chunks.

    The answer always carries sources. The walking-skeleton generator ignores `chunks`.
    """

    @abstractmethod
    def generate(self, query: Query, chunks: Sequence[ScoredChunk] = ()) -> Answer: ...
