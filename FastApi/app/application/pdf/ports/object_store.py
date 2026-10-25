from abc import ABC, abstractmethod


class ObjectStore(ABC):
    """Immutable, content-addressed storage for original files."""

    @abstractmethod
    def put(self, data: bytes) -> str:
        """Store bytes and return their key (derived from the SHA-256). Re-putting is a no-op."""

    @abstractmethod
    def get(self, key: str) -> bytes: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...
