from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.value_objects import Embedding


class Embedder(ABC):
    """Outbound port: text to vector. `version` identifies the vector space."""

    @property
    @abstractmethod
    def version(self) -> str: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @abstractmethod
    def embed(self, text: str) -> Embedding: ...

    def embed_many(self, texts: Sequence[str]) -> list[Embedding]:
        return [self.embed(t) for t in texts]
