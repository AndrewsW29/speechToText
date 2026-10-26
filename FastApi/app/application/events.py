"""Domain events and a tiny in-process bus. Subscriber failures never break the request."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AnswerDelivered:
    query_id: str
    intent: str | None
    source_ids: tuple[str, ...]
    confidence: float | None


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable[[Any], None]) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event: object) -> None:
        for handler in self._subscribers[type(event)]:
            try:
                handler(event)
            except Exception:
                logger.exception("event handler failed")
