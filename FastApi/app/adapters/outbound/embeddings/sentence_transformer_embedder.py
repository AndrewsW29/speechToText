from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.application.errors import ApplicationError
from app.application.ports.embedder import Embedder
from app.domain.value_objects import Embedding


class SentenceTransformerEmbedder(Embedder):
    """Pretrained embedder (extra 'embeddings'). The model loads lazily on first use."""

    def __init__(
        self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", dimension: int = 384
    ) -> None:
        self._model_name = model_name
        self._dimension = dimension
        self._model: Any = None

    @property
    def version(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def _load(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - optional extra
                raise ApplicationError(
                    "sentence-transformers is not installed (extra 'embeddings')"
                ) from exc
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed(self, text: str) -> Embedding:
        return self.embed_many([text])[0]

    def embed_many(self, texts: Sequence[str]) -> list[Embedding]:
        vectors = self._load().encode(list(texts), normalize_embeddings=True)
        return [Embedding(tuple(float(x) for x in v)) for v in vectors]
