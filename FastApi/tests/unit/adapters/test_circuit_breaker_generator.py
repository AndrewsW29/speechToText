from collections.abc import Sequence

import pytest
from app.adapters.outbound.answer.circuit_breaker_generator import CircuitBreakerGenerator
from app.application.errors import GenerationError
from app.application.ports.answer_generator import AnswerGenerator
from app.domain.entities import Answer, Query, Source
from app.domain.retrieval import ScoredChunk
from app.domain.value_objects import Transcript

QUERY = Query("q", Transcript("how do I make a controller"))


class Scripted(AnswerGenerator):
    def __init__(self, label: str) -> None:
        self.label, self.fail, self.calls = label, False, 0

    def generate(self, query: Query, chunks: Sequence[ScoredChunk] = ()) -> Answer:
        self.calls += 1
        if self.fail:
            raise GenerationError("down")
        return Answer(self.label, (Source("s", "S"),))


class Clock:
    now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def parts() -> tuple[CircuitBreakerGenerator, Scripted, Scripted, Clock]:
    primary, fallback, clock = Scripted("llm"), Scripted("snippets"), Clock()
    breaker = CircuitBreakerGenerator(
        primary, fallback, failure_threshold=2, reset_seconds=30, clock=clock
    )
    return breaker, primary, fallback, clock


def test_closed_uses_the_primary(parts) -> None:  # type: ignore[no-untyped-def]
    breaker, _primary, fallback, _ = parts
    assert breaker.generate(QUERY).text == "llm"
    assert (breaker.state, fallback.calls) == ("closed", 0)


def test_a_failure_falls_back_and_threshold_opens_the_circuit(parts) -> None:  # type: ignore[no-untyped-def]
    breaker, primary, _fallback, _ = parts
    primary.fail = True
    assert breaker.generate(QUERY).text == "snippets"
    assert breaker.state == "closed"
    breaker.generate(QUERY)
    assert breaker.state == "open"
    primary.calls = 0
    assert breaker.generate(QUERY).text == "snippets"
    assert primary.calls == 0  # open: primary is not even tried


def test_half_open_probe_success_closes_failure_reopens(parts) -> None:  # type: ignore[no-untyped-def]
    breaker, primary, _, clock = parts
    primary.fail = True
    breaker.generate(QUERY)
    breaker.generate(QUERY)
    clock.now = 31
    assert breaker.state == "half-open"
    breaker.generate(QUERY)  # probe fails
    assert breaker.state == "open"
    clock.now = 100
    primary.fail = False
    assert breaker.generate(QUERY).text == "llm"
    assert breaker.state == "closed"


def test_success_resets_the_failure_count(parts) -> None:  # type: ignore[no-untyped-def]
    breaker, primary, _, _ = parts
    primary.fail = True
    breaker.generate(QUERY)
    primary.fail = False
    breaker.generate(QUERY)
    primary.fail = True
    breaker.generate(QUERY)
    assert breaker.state == "closed"
