from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

from app.application.ports.cache import Cache
from app.application.ports.embedder import Embedder
from app.domain.value_objects import Embedding


class CachedEmbedder(Embedder):
    """Decorator caching embeddings by (embedder version, text hash)."""

    def __init__(self, inner: Embedder, cache: Cache, ttl_seconds: int = 86400) -> None:
        self._inner = inner
        self._cache = cache
        self._ttl = ttl_seconds

    @property
    def version(self) -> str:
        return self._inner.version

    @property
    def dimension(self) -> int:
        return self._inner.dimension

    def _key(self, text: str) -> str:
        return f"emb:{self._inner.version}:{hashlib.sha256(text.encode()).hexdigest()}"

    def embed(self, text: str) -> Embedding:
        key = self._key(text)
        if (raw := self._cache.get(key)) is not None:
            return Embedding(tuple(json.loads(raw)))
        embedding = self._inner.embed(text)
        self._cache.set(key, json.dumps(embedding.values).encode(), self._ttl)
        return embedding

    def embed_many(self, texts: Sequence[str]) -> list[Embedding]:
        return [self.embed(t) for t in texts]
