import pytest
from app.adapters.outbound.stt.factory import ForbiddenEngineError, TranscriberFactory
from app.adapters.outbound.stt.fake_transcriber import DEFAULT_TEXT, FakeSttTranscriber
from app.application.errors import InvalidAudioError
from app.config import Settings


def test_returns_a_deterministic_transcript_for_any_non_empty_audio() -> None:
    t = FakeSttTranscriber()
    assert t.transcribe(b"\x1a\x45\xdf\xa3 a").text == DEFAULT_TEXT
    assert t.transcribe(b"completely different bytes").text == DEFAULT_TEXT


def test_language_hint_is_honoured_and_defaults_to_english() -> None:
    t = FakeSttTranscriber()
    assert t.transcribe(b"x").language is not None and t.transcribe(b"x").language.code == "en"  # type: ignore[union-attr]
    assert t.transcribe(b"x", "es").language.code == "es"  # type: ignore[union-attr]


def test_rejects_empty_audio() -> None:
    with pytest.raises(InvalidAudioError):
        FakeSttTranscriber().transcribe(b"")


def test_custom_text_comes_from_settings() -> None:
    settings = Settings(stt_engine="fake", fake_stt_text="explain dependency injection")
    assert (
        TranscriberFactory.create(settings).transcribe(b"x").text == "explain dependency injection"
    )


def test_factory_builds_the_fake_engine_outside_production() -> None:
    assert isinstance(
        TranscriberFactory.create(Settings(stt_engine="fake", environment="local")),
        FakeSttTranscriber,
    )


@pytest.mark.parametrize("environment", ["production", "Production", "prod"])
def test_factory_refuses_the_fake_engine_in_production(environment: str) -> None:
    with pytest.raises(ForbiddenEngineError):
        TranscriberFactory.create(Settings(stt_engine="fake", environment=environment))
