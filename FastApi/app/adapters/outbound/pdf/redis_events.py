"""Stage events in a Redis list per document: replayable, ordered, expiring."""

from __future__ import annotations

import json
import logging
from typing import Any

from redis import Redis

from app.application.pdf.ports.event_publisher import EventPublisher, EventReader

logger = logging.getLogger(__name__)
SEVEN_DAYS = 7 * 24 * 3600


class RedisEvents(EventPublisher, EventReader):
    def __init__(self, client: Redis, ttl_seconds: int = SEVEN_DAYS) -> None:
        self._client = client
        self._ttl = ttl_seconds

    @staticmethod
    def _key(document_id: str) -> str:
        return f"pdf:events:{document_id}"

    def publish(self, document_id: str, stage: str, **fields: Any) -> None:
        """Best effort: losing a progress event must never fail the ingestion itself."""
        try:
            key = self._key(document_id)
            self._client.rpush(
                key, json.dumps({"document_id": document_id, "stage": stage, **fields})
            )
            self._client.expire(key, self._ttl)
        except (OSError, ConnectionError):
            logger.warning("could not publish %s event for %s", stage, document_id)

    def read(self, document_id: str, after: int = 0) -> list[dict[str, Any]]:
        raw: list[Any] = self._client.lrange(self._key(document_id), after, -1)  # type: ignore[assignment]
        return [{"seq": after + i + 1, **json.loads(item)} for i, item in enumerate(raw)]
