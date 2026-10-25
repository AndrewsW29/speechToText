from __future__ import annotations


class FakeRedis:
    """The few list commands the event adapter needs."""

    def __init__(self) -> None:
        self.lists: dict[str, list[bytes]] = {}
        self.expiries: dict[str, int] = {}

    def rpush(self, key: str, value: bytes | str) -> int:
        self.lists.setdefault(key, []).append(value if isinstance(value, bytes) else value.encode())
        return len(self.lists[key])

    def lrange(self, key: str, start: int, stop: int) -> list[bytes]:
        items = self.lists.get(key, [])
        return items[start:] if stop == -1 else items[start : stop + 1]

    def expire(self, key: str, seconds: int) -> bool:
        self.expiries[key] = seconds
        return True
