"""Retry transient failures with exponential backoff; park the rest in the dead-letter queue."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from app.application.errors import TransientError
from app.application.pdf.ports.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


def is_transient(exc: BaseException) -> bool:
    return isinstance(exc, TransientError | ConnectionError | TimeoutError)


def backoff_seconds(attempt: int, base: float = 2.0, cap: float = 60.0) -> float:
    """attempt 0 -> base, 1 -> 2*base, ... capped."""
    return float(min(cap, base * (2**attempt)))


def run_with_retries(
    fn: Callable[[], object],
    document_id: str,
    repository: DocumentRepository,
    max_attempts: int = 3,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Returns "ok", "failed" (permanent error) or "dead_lettered" (transient errors exhausted)."""
    for attempt in range(1, max_attempts + 1):
        try:
            fn()
            return "ok"
        except Exception as exc:
            if not is_transient(exc):
                logger.warning(
                    "document %s failed permanently: %s", document_id, type(exc).__name__
                )
                return "failed"
            if attempt == max_attempts:
                repository.dead_letter(document_id, type(exc).__name__, attempt)
                logger.error("document %s dead-lettered after %d attempts", document_id, attempt)
                return "dead_lettered"
            sleep(backoff_seconds(attempt - 1))
    return "failed"  # pragma: no cover - loop always returns
