from app.adapters.outbound.embeddings.cached_embedder import CachedEmbedder
from app.adapters.outbound.rerank.score_reranker import ScoreReranker
from app.domain.entities import KnowledgeChunk
from app.domain.retrieval import ScoredChunk

from tests.fakes import FakeEmbedder


def _hit(i: str, score: float) -> ScoredChunk:
    return ScoredChunk(KnowledgeChunk(i, "text " + i, "java"), score)


def test_score_reranker_sorts_desc_truncates_and_breaks_ties_by_id() -> None:
    out = ScoreReranker().rerank(
        "q", [_hit("b", 0.5), _hit("a", 0.5), _hit("c", 0.9), _hit("d", 0.1)], 3
    )
    assert [h.chunk.id for h in out] == ["c", "a", "b"]


class DictCache:
    def __init__(self) -> None:
        self.data: dict[str, bytes] = {}

    def get(self, key: str) -> bytes | None:
        return self.data.get(key)

    def set(self, key: str, value: bytes, ttl_seconds: int) -> None:
        self.data[key] = value


def test_cached_embedder_hits_inner_once_per_text() -> None:
    inner = FakeEmbedder()
    cached = CachedEmbedder(inner, DictCache(), ttl_seconds=60)
    first, second = cached.embed("create a controller"), cached.embed("create a controller")
    assert first == second and inner.calls == 1
    assert cached.version == inner.version and cached.dimension == inner.dimension


def test_cache_key_includes_embedder_version() -> None:
    cache = DictCache()
    CachedEmbedder(FakeEmbedder(), cache, 60).embed("x")
    assert all(FakeEmbedder.version in k for k in cache.data)


def test_embed_many_only_computes_misses() -> None:
    inner, cache = FakeEmbedder(), DictCache()
    cached = CachedEmbedder(inner, cache, 60)
    cached.embed("a")
    cached.embed_many(["a", "b", "a"])
    assert inner.calls == 2
