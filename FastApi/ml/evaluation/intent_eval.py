"""Evaluate an intent/slot model (in memory or an exported version) into gate metrics."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from ml.evaluation.run_eval import evaluate
from ml.training.common.datasets import encode
from ml.training.intent.calibrate import apply_temperature


class Predictor:
    """Wraps a callable returning (intent_logits, slot_logits) for a batch of token ids."""

    def __init__(
        self,
        logits_fn: Any,
        vocab: Mapping[str, int],
        intents: Sequence[str],
        slot_tags: Sequence[str],
        temperature: float,
        max_len: int,
    ) -> None:
        self._fn, self._vocab, self._intents = logits_fn, vocab, list(intents)
        self._tags, self._temperature, self._max_len = list(slot_tags), temperature, max_len

    def logits(self, rows: Sequence[Mapping[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
        x = np.array([encode(r, self._vocab, self._max_len) for r in rows], dtype="int32")
        intent, slots = self._fn(x)
        return np.asarray(intent), np.asarray(slots)

    def predict(self, rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        intent_logits, slot_logits = self.logits(rows)
        probs = apply_temperature(intent_logits, self._temperature)
        out = []
        for row, p, s in zip(rows, probs, slot_logits, strict=True):
            n = len(row["tokens"])
            tags = [self._tags[int(i)] for i in s[: min(n, self._max_len)].argmax(axis=-1)]
            out.append(
                {
                    "intent": self._intents[int(p.argmax())],
                    "confidence": float(p.max()),
                    "tags": tags + ["O"] * (n - len(tags)),
                }
            )
        return out


def keras_predictor(
    model: Any, vocab, intents, slot_tags, temperature: float, max_len: int
) -> Predictor:  # type: ignore[no-untyped-def]
    def fn(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        out = model(x, training=False)
        return np.asarray(out["intent"]), np.asarray(out["slots"])

    return Predictor(fn, vocab, intents, slot_tags, temperature, max_len)


def load_predictor(version_dir: Path) -> Predictor:
    """Load an exported SavedModel version plus its sidecar files."""
    import tensorflow as tf

    labels = json.loads((version_dir / "labels.json").read_text())
    signature = tf.saved_model.load(str(version_dir)).signatures["serving_default"]

    def fn(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        out = signature(tokens=tf.constant(x))
        return out["intent"].numpy(), out["slots"].numpy()

    return Predictor(
        fn,
        json.loads((version_dir / "vocab.json").read_text()),
        labels["intents"],
        labels["slot_tags"],
        float(json.loads((version_dir / "temperature.json").read_text())["temperature"]),
        int(labels["max_len"]),
    )


def evaluate_predictor(predictor: Predictor, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return evaluate(rows, predictor.predict(rows))
