"""When the LLM is down, questions still get a snippet answer from retrieval."""

import httpx
from app.adapters.outbound.answer.circuit_breaker_generator import CircuitBreakerGenerator
from app.adapters.outbound.answer.ollama_answer_generator import OllamaAnswerGenerator
from app.adapters.outbound.answer.snippet_answer_generator import SnippetAnswerGenerator
from app.adapters.outbound.rerank.score_reranker import ScoreReranker
from app.application.services.retriever import Retriever
from app.application.use_cases.ask_question import AskQuestion
from app.domain.entities import KnowledgeChunk
from app.domain.retrieval import IndexedChunk

from tests.fakes import FakeEmbedder, FakeTranscriber, InMemoryVectorStore


def _use_case(handler) -> AskQuestion:  # type: ignore[no-untyped-def]
    embedder, store = FakeEmbedder(), InMemoryVectorStore()
    text = "A RestController exposes the service over HTTP"
    store.upsert(
        [
            IndexedChunk(
                KnowledgeChunk("c1", text, "java", source_url="https://d/c1"), embedder.embed(text)
            )
        ]
    )
    llm = OllamaAnswerGenerator(
        httpx.Client(transport=httpx.MockTransport(handler), base_url="http://ollama"), "m"
    )
    generator = CircuitBreakerGenerator(llm, SnippetAnswerGenerator(), failure_threshold=1)
    return AskQuestion(
        FakeTranscriber("rest controller"),
        generator,
        Retriever(embedder, store, ScoreReranker(), top_k=3),
    )


def test_llm_down_still_returns_a_sourced_snippet_answer() -> None:
    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    result = _use_case(down).execute(b"audio")
    assert result.answer is not None
    assert "RestController" in result.answer.text and result.answer.sources


def test_llm_up_returns_the_generated_text_with_the_same_sources() -> None:
    def up(request: httpx.Request) -> httpx.Response:
        assert "RestController" in request.content.decode()  # RAG prompt carries the context
        return httpx.Response(200, json={"response": "Annotate the class with @RestController."})

    result = _use_case(up).execute(b"audio")
    assert result.answer is not None
    assert result.answer.text.startswith("Annotate")
    assert [s.id for s in result.answer.sources] == ["c1"]
