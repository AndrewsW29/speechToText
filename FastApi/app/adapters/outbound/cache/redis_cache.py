from __future__ import annotations

from redis import Redis


class RedisCache:
    """Byte cache over Redis; satisfies the application `Cache` protocol."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    def get(self, key: str) -> bytes | None:
        value = self._client.get(key)
        return value if isinstance(value, bytes) else None

    def set(self, key: str, value: bytes, ttl_seconds: int) -> None:
        self._client.set(key, value, ex=ttl_seconds)
