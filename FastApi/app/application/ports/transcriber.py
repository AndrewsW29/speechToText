from abc import ABC, abstractmethod

from app.domain.value_objects import Transcript


class Transcriber(ABC):
    """Outbound port: speech to text."""

    @abstractmethod
    def transcribe(self, audio: bytes, language: str | None = None) -> Transcript:
        """Convert audio bytes to a transcript.

        Raises InvalidAudioError for empty audio and TranscriptionError for engine failures.
        """
