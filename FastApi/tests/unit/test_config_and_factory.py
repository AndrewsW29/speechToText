import pytest
from app.adapters.outbound.stt.factory import TranscriberFactory, UnknownTranscriberError
from app.adapters.outbound.stt.faster_whisper_transcriber import FasterWhisperTranscriber
from app.application.errors import InvalidAudioError
from app.config import Settings


def test_settings_read_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VA_MAX_AUDIO_BYTES", "123")
    monkeypatch.setenv("VA_DATABASE_URL", "postgresql+asyncpg://u:pa55w0rd-value@h/db")
    s = Settings()
    assert s.max_audio_bytes == 123
    assert "pa55w0rd-value" not in repr(s)  # secrets are masked


def test_factory_creates_whisper_lazily() -> None:
    assert isinstance(
        TranscriberFactory.create(Settings(stt_engine="whisper")), FasterWhisperTranscriber
    )


def test_factory_rejects_unknown_engine() -> None:
    with pytest.raises(UnknownTranscriberError):
        TranscriberFactory.create(Settings(stt_engine="nope"))


def test_whisper_rejects_empty_audio_without_loading_model() -> None:
    with pytest.raises(InvalidAudioError):
        FasterWhisperTranscriber().transcribe(b"")


class _Seg:
    def __init__(self, text: str) -> None:
        self.text = text


class _Info:
    language = "en"


class _FakeModel:
    def __init__(self, segments: list[str], fail: bool = False) -> None:
        self._segments, self._fail = segments, fail

    def transcribe(self, *_a: object, **_k: object) -> tuple[list[_Seg], _Info]:
        if self._fail:
            raise RuntimeError("cuda exploded")
        return [_Seg(s) for s in self._segments], _Info()


def _adapter(model: _FakeModel) -> FasterWhisperTranscriber:
    t = FasterWhisperTranscriber()
    t._model = model  # inject a fake CTranslate2 model
    return t


def test_whisper_joins_segments_and_reports_language() -> None:
    result = _adapter(_FakeModel([" how do I ", "create a service "])).transcribe(b"x")
    assert result.text == "how do I create a service" and result.language is not None
    assert result.language.code == "en"


def test_whisper_without_speech_is_a_transcription_error() -> None:
    from app.application.errors import TranscriptionError

    with pytest.raises(TranscriptionError):
        _adapter(_FakeModel([])).transcribe(b"x")


def test_whisper_engine_errors_do_not_leak_details() -> None:
    from app.application.errors import TranscriptionError

    with pytest.raises(TranscriptionError) as err:
        _adapter(_FakeModel([], fail=True)).transcribe(b"x")
    assert "cuda" not in str(err.value)
