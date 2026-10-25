from typing import Protocol


class Cache(Protocol):
    """Minimal byte cache port (Redis in production)."""

    def get(self, key: str) -> bytes | None: ...

    def set(self, key: str, value: bytes, ttl_seconds: int) -> None: ...
