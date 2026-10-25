from app.application.ports.transcriber import Transcriber
from app.config import Settings

PRODUCTION_NAMES = frozenset({"production", "prod"})


class UnknownTranscriberError(ValueError):
    pass


class ForbiddenEngineError(ValueError):
    """An engine that must not run in this environment was requested."""


class TranscriberFactory:
    """Creates the configured STT adapter (Factory pattern); new engines add one branch."""

    @staticmethod
    def create(settings: Settings) -> Transcriber:
        engine = settings.stt_engine.lower()
        if engine == "whisper":
            from app.adapters.outbound.stt.faster_whisper_transcriber import (
                FasterWhisperTranscriber,
            )

            return FasterWhisperTranscriber(model_size=settings.whisper_model_size)
        if engine == "fake":
            if settings.environment.lower() in PRODUCTION_NAMES:
                raise ForbiddenEngineError("the fake STT engine cannot run in production")
            from app.adapters.outbound.stt.fake_transcriber import DEFAULT_TEXT, FakeSttTranscriber

            return FakeSttTranscriber(settings.fake_stt_text or DEFAULT_TEXT)
        raise UnknownTranscriberError(f"unknown STT engine: {settings.stt_engine!r}")
