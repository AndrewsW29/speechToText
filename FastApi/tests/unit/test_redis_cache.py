from app.adapters.outbound.cache.redis_cache import RedisCache


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, tuple[bytes, int]] = {}

    def get(self, key: str) -> bytes | None:
        return self.store.get(key, (None, 0))[0]

    def set(self, key: str, value: bytes, ex: int | None = None) -> None:
        self.store[key] = (value, ex or 0)


def test_redis_cache_roundtrip_with_ttl() -> None:
    redis = FakeRedis()
    cache = RedisCache(redis)  # type: ignore[arg-type]
    assert cache.get("k") is None
    cache.set("k", b"v", 30)
    assert cache.get("k") == b"v" and redis.store["k"][1] == 30
