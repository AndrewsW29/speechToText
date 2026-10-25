"""Deterministic STT stand-in for CI, local development and Postman runs. Never for production."""

from app.application.errors import InvalidAudioError
from app.application.ports.transcriber import Transcriber
from app.domain.value_objects import Language, Transcript

DEFAULT_TEXT = "how do I create a controller and a service in Java"


class FakeSttTranscriber(Transcriber):
    def __init__(self, text: str = DEFAULT_TEXT) -> None:
        self._text = text

    def transcribe(self, audio: bytes, language: str | None = None) -> Transcript:
        if not audio:
            raise InvalidAudioError("audio payload is empty")
        return Transcript(text=self._text, language=Language(language or "en"))
