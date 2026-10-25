"""TF Serving REST adapter: tokenize, call the model, apply temperature, decode BIO tags."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.application.errors import ClassificationError
from app.application.ports.intent_classifier import IntentClassifier
from app.application.services.entity_decoder import decode_entities
from app.application.services.tokenizer import tokenize
from app.domain.entities import Intent
from app.domain.value_objects import Confidence

PAD, UNK = "<pad>", "<unk>"


@dataclass(frozen=True, slots=True)
class ModelMeta:
    """Everything needed to talk to one exported model version (stored next to the SavedModel)."""

    vocab: dict[str, int]
    intents: list[str]
    slot_tags: list[str]
    temperature: float
    max_len: int

    @classmethod
    def load(cls, version_dir: Path) -> ModelMeta:
        labels = json.loads((version_dir / "labels.json").read_text())
        return cls(
            vocab=json.loads((version_dir / "vocab.json").read_text()),
            intents=labels["intents"],
            slot_tags=labels["slot_tags"],
            temperature=float(
                json.loads((version_dir / "temperature.json").read_text())["temperature"]
            ),
            max_len=int(labels["max_len"]),
        )


def _softmax(logits: Sequence[float], temperature: float) -> list[float]:
    scaled = [x / temperature for x in logits]
    top = max(scaled)
    exps = [math.exp(x - top) for x in scaled]
    total = sum(exps)
    return [e / total for e in exps]


class TFServingIntentClassifier(IntentClassifier):
    def __init__(
        self, client: httpx.Client, model_name: str, meta: ModelMeta, label: str | None = None
    ) -> None:
        self._client = client
        self._meta = meta
        path = f"/v1/models/{model_name}" + (f"/labels/{label}" if label else "")
        self._url = f"{path}:predict"

    def classify(self, text: str) -> Intent:
        tokens = tokenize(text)
        if not tokens:
            raise ClassificationError("nothing to classify")
        ids = [self._meta.vocab.get(t, self._meta.vocab[UNK]) for t in tokens][: self._meta.max_len]
        padded = ids + [self._meta.vocab[PAD]] * (self._meta.max_len - len(ids))
        try:
            response = self._client.post(self._url, json={"instances": [{"tokens": padded}]})
            response.raise_for_status()
            prediction = response.json()["predictions"][0]
            probs = _softmax(prediction["intent"], self._meta.temperature)
            best = max(range(len(probs)), key=probs.__getitem__)
            tag_rows = prediction["slots"][: len(ids)]
            tags = [self._meta.slot_tags[max(range(len(r)), key=r.__getitem__)] for r in tag_rows]
            return Intent(
                name=self._meta.intents[best],
                confidence=Confidence(min(1.0, probs[best])),
                entities=decode_entities(tokens[: len(ids)], tags),
            )
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise ClassificationError("intent classifier unavailable") from exc
