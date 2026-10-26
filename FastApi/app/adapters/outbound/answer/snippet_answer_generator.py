"""Retrieval-only answer: the best chunks, each cited as a source (no LLM)."""

from collections.abc import Sequence

from app.application.ports.answer_generator import AnswerGenerator
from app.application.services.answer_builder import AnswerBuilder
from app.domain.entities import Answer, Query
from app.domain.retrieval import ScoredChunk


class SnippetAnswerGenerator(AnswerGenerator):
    def __init__(self, builder: AnswerBuilder | None = None) -> None:
        self._builder = builder or AnswerBuilder()

    def generate(self, query: Query, chunks: Sequence[ScoredChunk] = ()) -> Answer:
        top = self._builder.top(chunks)
        text = "\n\n".join(f"{i}. {hit.chunk.text}" for i, hit in enumerate(top, start=1))
        return self._builder.build(text, top)
