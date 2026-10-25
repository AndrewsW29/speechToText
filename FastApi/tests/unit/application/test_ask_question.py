import pytest
from app.adapters.outbound.answer.fixed_answer_generator import FixedAnswerGenerator
from app.application.errors import InvalidAudioError
from app.application.use_cases.ask_question import AskQuestion

from tests.fakes import FakeTranscriber


def _use_case(transcriber: FakeTranscriber | None = None) -> tuple[AskQuestion, FakeTranscriber]:
    t = transcriber or FakeTranscriber("how do I create a controller in Java")
    return AskQuestion(transcriber=t, generator=FixedAnswerGenerator()), t


def test_returns_transcript_and_answer_with_sources() -> None:
    uc, _ = _use_case()
    result = uc.execute(b"audio-bytes")
    assert result.query.transcript.text == "how do I create a controller in Java"
    assert result.answer.sources, "an answer must always cite a source"
    assert "controller" in result.answer.text.lower()


def test_passes_audio_to_the_transcriber() -> None:
    uc, t = _use_case()
    uc.execute(b"abc")
    assert t.received == [b"abc"]


def test_each_question_gets_a_unique_id() -> None:
    uc, _ = _use_case()
    assert uc.execute(b"a").query.id != uc.execute(b"a").query.id


def test_empty_audio_is_rejected() -> None:
    uc, _ = _use_case()
    with pytest.raises(InvalidAudioError):
        uc.execute(b"")
