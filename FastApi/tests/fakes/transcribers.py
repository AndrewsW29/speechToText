from app.application.errors import InvalidAudioError
from app.application.ports.transcriber import Transcriber
from app.domain.value_objects import Language, Transcript


class FakeTranscriber(Transcriber):
    """In-memory transcriber returning a canned transcript; records the audio it received."""

    def __init__(
        self, text: str = "how do I create a controller in Java", language: str = "en"
    ) -> None:
        self._text = text
        self._language = language
        self.received: list[bytes] = []

    def transcribe(self, audio: bytes, language: str | None = None) -> Transcript:
        if not audio:
            raise InvalidAudioError("audio payload is empty")
        self.received.append(audio)
        return Transcript(text=self._text, language=Language(language or self._language))
