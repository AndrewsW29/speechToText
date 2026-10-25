"""Walking-skeleton generator: a fixed, sourced answer (replaced by retrieval in US2)."""

from collections.abc import Sequence

from app.application.ports.answer_generator import AnswerGenerator
from app.domain.entities import Answer, Query, Source
from app.domain.retrieval import ScoredChunk


class FixedAnswerGenerator(AnswerGenerator):
    def generate(self, query: Query, chunks: Sequence[ScoredChunk] = ()) -> Answer:
        return Answer(
            text=(
                f"You asked: {query.transcript.text}. In Spring, create a @Service for the "
                "business logic and a @RestController that calls it; the controller exposes "
                "the service over HTTP."
            ),
            sources=(
                Source(
                    id="spring-web-rest",
                    title="Spring Docs: Building a REST service",
                    url="https://spring.io/guides/gs/rest-service",
                ),
            ),
        )
