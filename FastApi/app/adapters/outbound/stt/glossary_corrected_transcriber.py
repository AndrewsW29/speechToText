from __future__ import annotations

from app.application.ports.transcriber import Transcriber
from app.application.services.glossary import GlossaryCorrector
from app.domain.value_objects import Transcript


class GlossaryCorrectedTranscriber(Transcriber):
    """Decorator: run the inner transcriber, then fix technical terms from the glossary."""

    def __init__(self, inner: Transcriber, corrector: GlossaryCorrector) -> None:
        self._inner = inner
        self._corrector = corrector

    def transcribe(self, audio: bytes, language: str | None = None) -> Transcript:
        transcript = self._inner.transcribe(audio, language)
        return Transcript(
            text=self._corrector.correct(transcript.text), language=transcript.language
        )
