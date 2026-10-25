import pytest
from app.domain.entities import Answer, Feedback, Intent, KnowledgeChunk, Query, Source
from app.domain.value_objects import Confidence, Transcript


def _source() -> Source:
    return Source(id="s1", title="Spring Docs", url="https://spring.io")


class TestSource:
    def test_kind_defaults_to_documentation(self) -> None:
        assert _source().kind == "documentation"

    def test_rejects_unknown_kind(self) -> None:
        with pytest.raises(ValueError):
            Source(id="s", title="t", kind="blog-spam")


class TestAnswer:
    def test_requires_at_least_one_source(self) -> None:
        with pytest.raises(ValueError, match="source"):
            Answer(text="use @RestController", sources=())

    def test_requires_text(self) -> None:
        with pytest.raises(ValueError):
            Answer(text=" ", sources=(_source(),))

    def test_valid_answer(self) -> None:
        a = Answer(text="use @RestController", sources=(_source(),))
        assert a.sources[0].id == "s1"


class TestQuery:
    def test_wraps_transcript(self) -> None:
        q = Query(id="q1", transcript=Transcript(text="hello"))
        assert q.transcript.text == "hello"

    def test_requires_id(self) -> None:
        with pytest.raises(ValueError):
            Query(id="", transcript=Transcript(text="hello"))


class TestIntent:
    def test_holds_name_confidence_entities(self) -> None:
        i = Intent(
            name="CREATE_CODE_ARTIFACT", confidence=Confidence(0.9), entities={"language": "java"}
        )
        assert i.entities["language"] == "java"

    def test_requires_name(self) -> None:
        with pytest.raises(ValueError):
            Intent(name="", confidence=Confidence(0.5))


class TestKnowledgeChunk:
    def test_requires_text_and_id(self) -> None:
        with pytest.raises(ValueError):
            KnowledgeChunk(id="", text="x", language="java")
        with pytest.raises(ValueError):
            KnowledgeChunk(id="c1", text="", language="java")


class TestFeedback:
    def test_accepts_up_and_down(self) -> None:
        assert Feedback(question_id="q1", vote="up").vote == "up"
        assert (
            Feedback(question_id="q1", vote="down", reason="wrong_language").reason
            == "wrong_language"
        )

    def test_rejects_unknown_vote(self) -> None:
        with pytest.raises(ValueError):
            Feedback(question_id="q1", vote="meh")

    def test_training_consent_defaults_to_false(self) -> None:
        assert Feedback(question_id="q1", vote="up").consent_training is False
