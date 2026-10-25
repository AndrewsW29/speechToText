from __future__ import annotations

import io
from typing import Any

from app.application.errors import InvalidAudioError, TranscriptionError
from app.application.ports.transcriber import Transcriber
from app.domain.value_objects import Language, Transcript


class FasterWhisperTranscriber(Transcriber):
    """faster-whisper (CTranslate2) adapter. The model loads lazily on first use."""

    def __init__(self, model_size: str = "small", compute_type: str = "int8") -> None:
        self._model_size = model_size
        self._compute_type = compute_type
        self._model: Any = None

    def _load(self) -> Any:
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:  # pragma: no cover - depends on optional extra
                raise TranscriptionError("faster-whisper is not installed (extra 'stt')") from exc
            self._model = WhisperModel(self._model_size, compute_type=self._compute_type)
        return self._model

    def transcribe(self, audio: bytes, language: str | None = None) -> Transcript:
        if not audio:
            raise InvalidAudioError("audio payload is empty")
        try:
            segments, info = self._load().transcribe(
                io.BytesIO(audio), language=language, vad_filter=True
            )
            text = " ".join(s.text.strip() for s in segments).strip()
        except TranscriptionError:
            raise
        except Exception as exc:  # engine errors must not leak internals
            raise TranscriptionError("speech-to-text failed") from exc
        if not text:
            raise TranscriptionError("no speech detected")
        return Transcript(text=text, language=Language(info.language) if info.language else None)
