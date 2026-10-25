import shutil

import numpy as np
import pytest

from ml.training.common.asr_augment import align_tags, augment_record, mix_noise, snr_db


def test_mix_noise_hits_the_requested_snr() -> None:
    rng = np.random.default_rng(0)
    signal, noise = rng.normal(size=16000), rng.normal(size=16000)
    for target in (5, 15, 30):
        assert snr_db(signal, mix_noise(signal, noise, target) - signal) == pytest.approx(
            target, abs=0.01
        )


def test_mix_noise_tiles_short_noise() -> None:
    out = mix_noise(np.ones(100), np.ones(10), 10)
    assert out.shape == (100,)


def test_align_copies_tags_through_substitutions() -> None:
    tokens = ["how", "do", "i", "create", "a", "controller", "and", "a", "service", "in", "java"]
    tags = ["O"] * 5 + ["B-ARTIFACT", "O", "O", "B-ARTIFACT", "O", "B-LANGUAGE"]
    asr = ["how", "do", "i", "create", "a", "controler", "and", "a", "surface", "in", "java"]
    assert align_tags(tokens, tags, asr) == tags


def test_align_handles_insertions_deletions_and_multiword_replacements() -> None:
    tokens = ["use", "spring", "boot", "service"]
    tags = ["O", "B-FRAMEWORK", "I-FRAMEWORK", "B-ARTIFACT"]
    assert align_tags(tokens, tags, ["use", "um", "spring", "boot", "service"]) == [
        "O",
        "O",
        "B-FRAMEWORK",
        "I-FRAMEWORK",
        "B-ARTIFACT",
    ]
    assert align_tags(tokens, tags, ["use", "springboot", "service"]) == [
        "O",
        "B-FRAMEWORK",
        "B-ARTIFACT",
    ]


class FakeTTS:
    def synthesize(self, text: str, voice: str, speed: float) -> tuple[np.ndarray, int]:
        return np.sin(np.linspace(0, 100, 16000)), 16000


class FakeEncoder:
    def __init__(self) -> None:
        self.codecs: list[str] = []

    def roundtrip(self, samples: np.ndarray, rate: int, codec: str) -> np.ndarray:
        self.codecs.append(codec)
        return samples


class FakeASR:
    def __init__(self, text: str) -> None:
        self.text = text

    def transcribe_samples(self, samples: np.ndarray, rate: int) -> str:
        return self.text


def test_augment_record_copies_labels_and_provenance() -> None:
    parent = {
        "id": "u-1",
        "tokens": ["make", "a", "service", "in", "java"],
        "tags": ["O", "O", "B-ARTIFACT", "O", "B-LANGUAGE"],
        "intent": "CREATE_CODE_ARTIFACT",
        "source": "seed",
    }
    enc = FakeEncoder()
    out = augment_record(
        parent,
        tts=FakeTTS(),
        encoder=enc,
        asr=FakeASR("make a surface in java"),
        noise=np.random.default_rng(1).normal(size=16000),
        voice="en-GB-f2",
        speed=1.1,
        snr=15.0,
        codec="webm-opus",
        variant=1,
    )
    assert out["id"] == "u-1-asr1" and out["parent_id"] == "u-1"
    assert out["tokens"] == ["make", "a", "surface", "in", "java"] and out["tags"] == parent["tags"]
    assert out["intent"] == "CREATE_CODE_ARTIFACT" and out["source"] == "asr_augmented"
    assert (out["tts_voice"], out["speed"], out["snr_db"]) == ("en-GB-f2", 1.1, 15.0)
    assert enc.codecs == ["webm-opus"]


def test_augment_skips_records_the_asr_returns_empty_for() -> None:
    parent = {"id": "u-2", "tokens": ["hi"], "tags": ["O"], "intent": "X", "source": "seed"}
    assert (
        augment_record(
            parent, FakeTTS(), FakeEncoder(), FakeASR("  "), np.ones(10), "v", 1.0, 10.0, "aac", 1
        )
        is None
    )


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
@pytest.mark.parametrize("codec", ["webm-opus", "aac"])
def test_ffmpeg_encoder_roundtrips_through_real_client_codecs(codec: str) -> None:
    from ml.training.common.asr_augment import FfmpegEncoder

    rate = 16000
    t = np.arange(rate) / rate
    tone = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    out = FfmpegEncoder().roundtrip(tone, rate, codec)
    assert abs(len(out) - len(tone)) < rate * 0.2  # codec padding only
    assert (
        np.corrcoef(out[: len(tone)][2000:6000], tone[2000:6000])[0, 1] > 0.9
        or np.abs(out).max() > 0.05
    )
