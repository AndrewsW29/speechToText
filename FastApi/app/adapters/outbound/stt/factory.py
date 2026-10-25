from app.application.ports.transcriber import Transcriber
from app.config import Settings


class UnknownTranscriberError(ValueError):
    pass


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
        raise UnknownTranscriberError(f"unknown STT engine: {settings.stt_engine!r}")
