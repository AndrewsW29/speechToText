import pytest
from app.adapters.outbound.answer.top_chunks_answer_generator import TopChunksAnswerGenerator
from app.application.errors import NoRelevantSourcesError
from app.application.services.retriever import Retriever
from app.application.use_cases.ask_question import AskQuestion
from app.domain.entities import KnowledgeChunk
from app.domain.retrieval import IndexedChunk, extract_filters

from tests.fakes import FakeEmbedder, FakeTranscriber, InMemoryVectorStore, ReverseReranker


def _index(store: InMemoryVectorStore, embedder: FakeEmbedder) -> None:
    rows = [
        ("c", "A RestController exposes the service over HTTP with GetMapping", "java", "spring"),
        (
            "s",
            "A Service class holds business logic and is injected with the constructor",
            "java",
            "spring",
        ),
        ("k", "Kotlin coroutines launch structured concurrency in a scope", "kotlin", None),
    ]
    store.upsert(
        [
            IndexedChunk(
                KnowledgeChunk(i, t, lang, fw, source_url=f"https://docs/{i}"), embedder.embed(t)
            )
            for i, t, lang, fw in rows
        ]
    )


@pytest.fixture
def parts() -> tuple[InMemoryVectorStore, FakeEmbedder]:
    store, embedder = InMemoryVectorStore(), FakeEmbedder()
    _index(store, embedder)
    return store, embedder


def _ask(parts, text: str, reranker=None) -> AskQuestion:  # type: ignore[no-untyped-def]
    store, embedder = parts
    from app.adapters.outbound.rerank.score_reranker import ScoreReranker

    retriever = Retriever(embedder, store, reranker or ScoreReranker(), top_k=3)
    return AskQuestion(FakeTranscriber(text), TopChunksAnswerGenerator(), retriever)


def test_answer_is_built_from_retrieved_chunks_with_sources(parts) -> None:  # type: ignore[no-untyped-def]
    result = _ask(parts, "how do I create a rest controller in Java").execute(b"a")
    assert "RestController" in result.answer.text
    assert result.answer.sources[0].url == "https://docs/c"


def test_entity_filters_exclude_other_languages(parts) -> None:  # type: ignore[no-untyped-def]
    result = _ask(parts, "explain coroutines in kotlin").execute(b"a")
    assert {s.id for s in result.answer.sources} == {"k"}


def test_reranker_order_is_honoured(parts) -> None:  # type: ignore[no-untyped-def]
    normal = _ask(parts, "controller service in java").execute(b"a").answer.sources
    reversed_ = (
        _ask(parts, "controller service in java", ReverseReranker()).execute(b"a").answer.sources
    )
    assert [s.id for s in reversed_] == [s.id for s in reversed(normal)]


def test_repository_hosts_are_classified_as_repository_sources() -> None:
    from app.adapters.outbound.answer.top_chunks_answer_generator import TopChunksAnswerGenerator
    from app.domain.entities import Query
    from app.domain.retrieval import ScoredChunk
    from app.domain.value_objects import Transcript

    hit = ScoredChunk(
        KnowledgeChunk(
            "g", "code", "java", source_url="https://github.com/acme/users/UserController.java"
        ),
        1.0,
    )
    answer = TopChunksAnswerGenerator().generate(Query("q", Transcript("x")), [hit])
    assert answer.sources[0].kind == "repository"


def test_no_hits_raises_instead_of_inventing_an_answer(parts) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(NoRelevantSourcesError):
        _ask(parts, "something about swift").execute(b"a")


def test_extract_filters_detects_language_and_framework() -> None:
    f = extract_filters("How do I create a controller in Java with Spring?")
    assert (f.language, f.framework) == ("java", "spring")
    assert extract_filters("what is dependency injection").language is None
