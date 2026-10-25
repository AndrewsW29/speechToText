import pytest
from app.adapters.outbound.answer.top_chunks_answer_generator import TopChunksAnswerGenerator
from app.adapters.outbound.rerank.score_reranker import ScoreReranker
from app.application.services.intent_router import default_router
from app.application.services.retriever import Retriever
from app.application.use_cases.ask_question import LANGUAGE_OPTIONS, AskQuestion
from app.domain.confidence_gate import ConfidenceGate
from app.domain.entities import KnowledgeChunk
from app.domain.retrieval import IndexedChunk

from tests.fakes import FakeClassifier, FakeEmbedder, FakeTranscriber, InMemoryVectorStore

ROWS = [
    ("j1", "A RestController exposes the service over HTTP", "java"),
    ("k1", "A Kotlin controller exposes the service over HTTP with coroutines", "kotlin"),
]


class CountingRetriever(Retriever):
    def __init__(self, *a, **k) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*a, **k)
        self.calls: list = []

    def retrieve(self, question, filters=None):  # type: ignore[no-untyped-def]
        self.calls.append(filters)
        return super().retrieve(question, filters)


def _build(
    classifier: FakeClassifier | None, text: str = "create a controller"
) -> tuple[AskQuestion, CountingRetriever]:
    embedder, store = FakeEmbedder(), InMemoryVectorStore()
    store.upsert(
        [
            IndexedChunk(KnowledgeChunk(i, t, lang, source_url=f"https://d/{i}"), embedder.embed(t))
            for i, t, lang in ROWS
        ]
    )
    retriever = CountingRetriever(embedder, store, ScoreReranker(), top_k=3)
    uc = AskQuestion(
        FakeTranscriber(text),
        TopChunksAnswerGenerator(),
        retriever,
        classifier,
        ConfidenceGate(),
        default_router(),
    )
    return uc, retriever


def test_confident_intent_runs_the_handler_with_entity_filters() -> None:
    uc, retriever = _build(
        FakeClassifier(
            "CREATE_CODE_ARTIFACT", 0.95, {"LANGUAGE": "kotlin", "ARTIFACT": "controller"}
        )
    )
    result = uc.execute(b"a")
    assert (
        result.status == "answer"
        and result.intent is not None
        and result.intent.name == "CREATE_CODE_ARTIFACT"
    )
    assert {s.id for s in result.answer.sources} == {"k1"}  # type: ignore[union-attr]
    assert retriever.calls[0].language == "kotlin"


def test_missing_language_asks_a_clarifying_question_with_option_chips() -> None:
    uc, retriever = _build(FakeClassifier("CREATE_CODE_ARTIFACT", 0.95, {"ARTIFACT": "controller"}))
    result = uc.execute(b"a")
    assert result.status == "clarify" and result.answer is None
    assert result.clarification is not None and result.clarification.options == LANGUAGE_OPTIONS
    assert retriever.calls == []


def test_profile_default_fills_the_missing_entity_before_the_gate() -> None:
    uc, retriever = _build(FakeClassifier("CREATE_CODE_ARTIFACT", 0.95, {"ARTIFACT": "controller"}))
    result = uc.execute(b"a", profile={"LANGUAGE": "java"})
    assert result.status == "answer" and retriever.calls[0].language == "java"
    assert result.intent is not None and result.intent.entities["LANGUAGE"] == "java"


def test_spoken_entities_override_profile_defaults() -> None:
    uc, retriever = _build(FakeClassifier("CREATE_CODE_ARTIFACT", 0.95, {"LANGUAGE": "kotlin"}))
    uc.execute(b"a", profile={"LANGUAGE": "java"})
    assert retriever.calls[0].language == "kotlin"


def test_out_of_scope_is_refused_without_retrieval() -> None:
    uc, retriever = _build(FakeClassifier("OUT_OF_SCOPE", 0.99))
    result = uc.execute(b"a")
    assert result.status == "abstain" and result.answer is None and result.message
    assert retriever.calls == []


def test_low_confidence_abstains_and_medium_confidence_clarifies() -> None:
    assert _build(FakeClassifier("EXPLAIN_CONCEPT", 0.3))[0].execute(b"a").status == "abstain"
    medium = _build(FakeClassifier("EXPLAIN_CONCEPT", 0.65))[0].execute(b"a")
    assert (
        medium.status == "clarify"
        and medium.clarification is not None
        and medium.clarification.options == []
    )


def test_meta_commands_skip_retrieval_and_return_the_command() -> None:
    uc, retriever = _build(FakeClassifier("META_COMMAND", 0.97), text="repeat that")
    result = uc.execute(b"a")
    assert result.status == "command" and result.message == "repeat that" and retriever.calls == []


def test_classifier_outage_degrades_to_the_ungated_path() -> None:
    uc, retriever = _build(FakeClassifier(fail=True), text="how do I create a controller in java")
    result = uc.execute(b"a")
    assert result.status == "answer" and result.intent is None and len(retriever.calls) == 1


def test_classifier_receives_the_transcript() -> None:
    clf = FakeClassifier("EXPLAIN_CONCEPT", 0.9)
    _build(clf, text="what is dependency injection")[0].execute(b"a")
    assert clf.seen == ["what is dependency injection"]


def test_no_classifier_keeps_the_original_behaviour() -> None:
    uc, retriever = _build(None, text="how do I create a controller in java")
    assert uc.execute(b"a").status == "answer" and len(retriever.calls) == 1


def test_retriever_prefers_explicit_filters_over_keyword_extraction() -> None:
    from app.domain.retrieval import SearchFilters

    embedder, store = FakeEmbedder(), InMemoryVectorStore()
    store.upsert(
        [IndexedChunk(KnowledgeChunk(i, t, lang), embedder.embed(t)) for i, t, lang in ROWS]
    )
    retriever = Retriever(embedder, store, ScoreReranker(), top_k=5)
    hits = retriever.retrieve("controller in java", SearchFilters(language="kotlin"))
    assert {h.chunk.language for h in hits} == {"kotlin"}
    assert pytest.approx(0) == 0


def test_framework_never_excludes_results_and_unknown_languages_are_not_used_as_filters() -> None:
    uc, retriever = _build(
        FakeClassifier("EXPLAIN_CONCEPT", 0.95, {"FRAMEWORK": "spring boot", "LANGUAGE": "jar va"})
    )
    result = uc.execute(b"a")
    assert result.status == "answer"
    assert retriever.calls[0].language is None and retriever.calls[0].framework is None
