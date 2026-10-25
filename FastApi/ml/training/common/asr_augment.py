"""ASR-in-the-loop augmentation: text -> TTS -> noise -> codec -> Whisper -> noisy text with gold labels."""

from __future__ import annotations

import difflib
import subprocess
from collections.abc import Sequence
from typing import Any, Protocol

import numpy as np

from ml.training.common.markup import tokenize

CODECS = {"webm-opus": ("libopus", "webm"), "aac": ("aac", "adts")}


class TextToSpeech(Protocol):
    def synthesize(self, text: str, voice: str, speed: float) -> tuple[np.ndarray, int]: ...


class Encoder(Protocol):
    def roundtrip(self, samples: np.ndarray, rate: int, codec: str) -> np.ndarray: ...


class SpeechToText(Protocol):
    def transcribe_samples(self, samples: np.ndarray, rate: int) -> str: ...


def snr_db(signal: np.ndarray, noise: np.ndarray) -> float:
    return float(10 * np.log10(np.mean(signal**2) / np.mean(noise**2)))


def mix_noise(signal: np.ndarray, noise: np.ndarray, snr: float) -> np.ndarray:
    """Add `noise` (tiled or trimmed to length) so the result has the requested SNR in dB."""
    reps = int(np.ceil(len(signal) / len(noise)))
    noise = np.tile(noise, reps)[: len(signal)]
    scale = np.sqrt(np.mean(signal**2) / (np.mean(noise**2) * 10 ** (snr / 10)))
    return signal + scale * noise


def align_tags(tokens: Sequence[str], tags: Sequence[str], asr_tokens: Sequence[str]) -> list[str]:
    """Carry gold BIO tags onto ASR tokens, tolerating substitutions, insertions and deletions."""
    out: list[str] = []
    matcher = difflib.SequenceMatcher(None, list(tokens), list(asr_tokens), autojunk=False)
    for op, a0, a1, b0, b1 in matcher.get_opcodes():
        if op == "equal":
            out.extend(tags[a0:a1])
        elif op == "insert":
            out.extend("O" for _ in range(b0, b1))
        elif op == "replace":
            first = tags[a0]
            label = first[2:] if first != "O" else None
            out.append(first)
            out.extend(f"I-{label}" if label else "O" for _ in range(b0 + 1, b1))
        # "delete": ASR dropped the tokens; nothing to emit
    return out


def augment_record(
    parent: dict[str, Any],
    tts: TextToSpeech,
    encoder: Encoder,
    asr: SpeechToText,
    noise: np.ndarray,
    voice: str,
    speed: float,
    snr: float,
    codec: str,
    variant: int,
) -> dict[str, Any] | None:
    samples, rate = tts.synthesize(" ".join(parent["tokens"]), voice, speed)
    noisy = mix_noise(samples, noise, snr)
    heard = asr.transcribe_samples(encoder.roundtrip(noisy, rate, codec), rate)
    asr_tokens = tokenize(heard)
    if not asr_tokens:
        return None
    parent_id = parent.get("parent_id", parent["id"])
    return {
        "id": f"{parent['id']}-asr{variant}",
        "parent_id": parent_id,
        "tokens": asr_tokens,
        "tags": align_tags(parent["tokens"], parent["tags"], asr_tokens),
        "intent": parent["intent"],
        "source": "asr_augmented",
        "tts_voice": voice,
        "speed": speed,
        "snr_db": snr,
        "codec": codec,
    }


class PiperTTS:
    """Local Piper CLI (`piper --model <voice.onnx> --output-raw`), 16-bit mono PCM."""

    def __init__(self, models_dir: str, rate: int = 22050) -> None:
        self._models_dir, self._rate = models_dir, rate

    def synthesize(self, text: str, voice: str, speed: float) -> tuple[np.ndarray, int]:
        result = subprocess.run(
            [
                "piper",
                "--model",
                f"{self._models_dir}/{voice}.onnx",
                "--output-raw",
                "--length-scale",
                str(1 / speed),
            ],
            input=text.encode(),
            capture_output=True,
            check=True,
        )
        pcm = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        return pcm, self._rate


class FfmpegEncoder:
    """Round-trips audio through a real client codec (WebM/Opus, AAC) with ffmpeg."""

    def roundtrip(self, samples: np.ndarray, rate: int, codec: str) -> np.ndarray:
        lib, container = CODECS[codec]
        raw = samples.astype(np.float32).tobytes()
        encoded = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-f",
                "f32le",
                "-ar",
                str(rate),
                "-ac",
                "1",
                "-i",
                "pipe:0",
                "-c:a",
                lib,
                "-f",
                container,
                "pipe:1",
            ],
            input=raw,
            capture_output=True,
            check=True,
        ).stdout
        decoded = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                "pipe:0",
                "-f",
                "f32le",
                "-ar",
                str(rate),
                "-ac",
                "1",
                "pipe:1",
            ],
            input=encoded,
            capture_output=True,
            check=True,
        ).stdout
        return np.frombuffer(decoded, dtype=np.float32)


class WhisperASR:
    """faster-whisper over in-memory 16 kHz samples."""

    def __init__(self, model_size: str = "small") -> None:
        from faster_whisper import WhisperModel

        self._model = WhisperModel(model_size, compute_type="int8")

    def transcribe_samples(self, samples: np.ndarray, rate: int) -> str:
        if rate != 16000:  # naive linear resample; fine for augmentation noise
            samples = np.interp(
                np.linspace(0, len(samples), int(len(samples) * 16000 / rate), endpoint=False),
                np.arange(len(samples)),
                samples,
            )
        segments, _ = self._model.transcribe(
            samples.astype(np.float32), language="en", vad_filter=False
        )
        return " ".join(s.text.strip() for s in segments)
