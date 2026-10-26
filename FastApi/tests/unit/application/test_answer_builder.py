import pytest
from app.application.errors import NoRelevantSourcesError
from app.application.services.answer_builder import AnswerBuilder
from app.domain.entities import KnowledgeChunk
from app.domain.retrieval import ScoredChunk


def _hit(
    i: str, score: float, url: str | None = "https://docs.spring.io/spring/rest-controller"
) -> ScoredChunk:
    return ScoredChunk(KnowledgeChunk(i, f"text {i}", "java", source_url=url), score)


def test_builds_an_answer_with_text_sources_and_snippets() -> None:
    answer = AnswerBuilder().build("Use @RestController.", [_hit("a", 0.8), _hit("b", 0.4)])
    assert answer.text == "Use @RestController."
    assert [s.id for s in answer.sources] == ["a", "b"]
    assert answer.snippets == ("text a", "text b")


def test_confidence_is_the_clamped_top_score() -> None:
    assert AnswerBuilder().build("x", [_hit("a", 0.8)]).confidence == pytest.approx(0.8)
    assert AnswerBuilder().build("x", [_hit("a", 7.0)]).confidence == 1.0
    assert AnswerBuilder().build("x", [_hit("a", -1.0)]).confidence == 0.0


def test_github_urls_are_repositories_and_titles_come_from_the_path() -> None:
    answer = AnswerBuilder().build("x", [_hit("a", 1, "https://github.com/o/r/blob/main/Foo")])
    assert answer.sources[0].kind == "repository"
    assert _hit
    assert AnswerBuilder().build("x", [_hit("b", 1)]).sources[0].title.endswith("rest controller")


def test_limits_sources_to_max_and_refuses_without_chunks() -> None:
    assert (
        len(AnswerBuilder(max_sources=2).build("x", [_hit(str(i), 1) for i in range(5)]).sources)
        == 2
    )
    with pytest.raises(NoRelevantSourcesError):
        AnswerBuilder().build("x", [])
