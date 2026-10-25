from __future__ import annotations

import threading
from typing import Any

from app.application.pdf.ports.event_publisher import EventPublisher, EventReader


class MemoryEvents(EventPublisher, EventReader):
    """Single-process event log for local development (use RedisEvents with workers)."""

    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def publish(self, document_id: str, stage: str, **fields: Any) -> None:
        with self._lock:
            items = self._events.setdefault(document_id, [])
            items.append(
                {"seq": len(items) + 1, "document_id": document_id, "stage": stage, **fields}
            )

    def read(self, document_id: str, after: int = 0) -> list[dict[str, Any]]:
        with self._lock:
            return [e for e in self._events.get(document_id, []) if e["seq"] > after]
