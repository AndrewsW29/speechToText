"""Ollama-backed answer generation with a RAG prompt, grounded in the retrieved chunks."""

from collections.abc import Sequence

import httpx

from app.application.errors import GenerationError
from app.application.ports.answer_generator import AnswerGenerator
from app.application.services.answer_builder import AnswerBuilder
from app.domain.entities import Answer, Query
from app.domain.retrieval import ScoredChunk

PROMPT = """You are a coding assistant. Answer the question using ONLY the context below.
If the context is not enough, say so. Be concise and include code when it helps.

Context:
{context}

Question: {question}
Answer:"""


class OllamaAnswerGenerator(AnswerGenerator):
    def __init__(
        self, client: httpx.Client, model: str, builder: AnswerBuilder | None = None
    ) -> None:
        self._client = client  # the client carries base_url and timeouts
        self._model = model
        self._builder = builder or AnswerBuilder()

    def generate(self, query: Query, chunks: Sequence[ScoredChunk] = ()) -> Answer:
        top = self._builder.top(chunks)
        context = "\n\n".join(f"[{i}] {h.chunk.text}" for i, h in enumerate(top, start=1))
        prompt = PROMPT.format(context=context, question=query.transcript.text)
        try:
            response = self._client.post(
                "/api/generate", json={"model": self._model, "prompt": prompt, "stream": False}
            )
            response.raise_for_status()
            text = str(response.json()["response"]).strip()
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise GenerationError("LLM unavailable") from exc
        if not text:
            raise GenerationError("LLM returned an empty answer")
        return self._builder.build(text, top)
