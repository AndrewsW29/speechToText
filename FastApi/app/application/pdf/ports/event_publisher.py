from abc import ABC, abstractmethod
from typing import Any

TERMINAL_STAGES = frozenset({"ready", "failed", "quarantined"})


class EventPublisher(ABC):
    @abstractmethod
    def publish(self, document_id: str, stage: str, **fields: Any) -> None: ...


class EventReader(ABC):
    @abstractmethod
    def read(self, document_id: str, after: int = 0) -> list[dict[str, Any]]:
        """Events with sequence number greater than `after`, oldest first (each has a `seq`)."""
