"""Contract every Transcriber adapter must satisfy (Liskov)."""

import importlib.util
from collections.abc import Callable

import pytest
from app.application.errors import InvalidAudioError
from app.application.ports.transcriber import Transcriber
from app.domain.value_objects import Transcript

from tests.fakes import FakeTranscriber

# Real audio fixture needed for the whisper adapter; it is exercised in the integration suite.
FACTORIES: list[Callable[[], Transcriber]] = [lambda: FakeTranscriber()]


@pytest.fixture(params=FACTORIES, ids=["fake"])
def transcriber(request: pytest.FixtureRequest) -> Transcriber:
    return request.param()


def test_returns_a_non_empty_transcript(transcriber: Transcriber) -> None:
    result = transcriber.transcribe(b"\x1aE\xdf\xa3audio")
    assert isinstance(result, Transcript)
    assert result.text.strip()


def test_rejects_empty_audio(transcriber: Transcriber) -> None:
    with pytest.raises(InvalidAudioError):
        transcriber.transcribe(b"")


def test_honours_language_hint(transcriber: Transcriber) -> None:
    result = transcriber.transcribe(b"\x1aE\xdf\xa3audio", language="es")
    assert result.language is not None and result.language.code == "es"


@pytest.mark.skipif(
    importlib.util.find_spec("faster_whisper") is None, reason="stt extra not installed"
)
def test_whisper_adapter_is_a_transcriber() -> None:
    from app.adapters.outbound.stt.faster_whisper_transcriber import FasterWhisperTranscriber

    assert issubclass(FasterWhisperTranscriber, Transcriber)
