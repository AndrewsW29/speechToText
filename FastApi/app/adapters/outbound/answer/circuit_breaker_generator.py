"""Circuit breaker around an unreliable generator, degrading to a fallback generator."""

import logging
import time
from collections.abc import Callable, Sequence

from app.application.errors import GenerationError
from app.application.ports.answer_generator import AnswerGenerator
from app.domain.entities import Answer, Query
from app.domain.retrieval import ScoredChunk

logger = logging.getLogger(__name__)


class CircuitBreakerGenerator(AnswerGenerator):
    """closed -> open after `failure_threshold` consecutive failures; half-open after
    `reset_seconds` lets one probe through; a successful probe closes, a failed one reopens."""

    def __init__(
        self,
        primary: AnswerGenerator,
        fallback: AnswerGenerator,
        failure_threshold: int = 3,
        reset_seconds: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._threshold = failure_threshold
        self._reset = reset_seconds
        self._clock = clock
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> str:
        if self._opened_at is None:
            return "closed"
        return "half-open" if self._clock() - self._opened_at >= self._reset else "open"

    def generate(self, query: Query, chunks: Sequence[ScoredChunk] = ()) -> Answer:
        if self.state == "open":
            return self._fallback.generate(query, chunks)
        try:
            answer = self._primary.generate(query, chunks)
        except GenerationError:
            self._failures += 1
            if self._opened_at is not None or self._failures >= self._threshold:
                self._opened_at = self._clock()  # (re)open
                logger.warning("answer generator circuit open")
            return self._fallback.generate(query, chunks)
        self._failures, self._opened_at = 0, None
        return answer
