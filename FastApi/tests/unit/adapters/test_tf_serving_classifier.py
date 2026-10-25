import json
import math

import httpx
import pytest
from app.adapters.outbound.intent.tf_serving_classifier import ModelMeta, TFServingIntentClassifier
from app.application.errors import ClassificationError

INTENTS = ["CREATE_CODE_ARTIFACT", "EXPLAIN_CONCEPT", "OUT_OF_SCOPE"]
SLOTS = ["O", "B-LANGUAGE", "I-LANGUAGE", "B-ARTIFACT"]
VOCAB = {"<pad>": 0, "<unk>": 1, "make": 2, "a": 3, "service": 4, "in": 5, "java": 6}


def _meta(temperature: float = 1.0) -> ModelMeta:
    return ModelMeta(
        vocab=VOCAB, intents=INTENTS, slot_tags=SLOTS, temperature=temperature, max_len=8
    )


def _client(
    intent_logits: list[float], slot_ids: list[int], seen: list[dict] | None = None
) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if seen is not None:
            seen.append({"url": str(request.url), "body": body})
        slots = [[1.0 if j == k else 0.0 for j in range(len(SLOTS))] for k in slot_ids]
        slots += [[1.0, 0.0, 0.0, 0.0]] * (8 - len(slot_ids))
        return httpx.Response(
            200, json={"predictions": [{"intent": intent_logits, "slots": slots}]}
        )

    return httpx.Client(transport=httpx.MockTransport(handler), base_url="http://tf")


def test_classifies_with_calibrated_confidence_and_decoded_entities() -> None:
    seen: list[dict] = []
    clf = TFServingIntentClassifier(
        _client([4.0, 0.0, -1.0], [0, 0, 3, 0, 1], seen), "intent", _meta()
    )
    intent = clf.classify("Make a service in Java")
    assert intent.name == "CREATE_CODE_ARTIFACT"
    assert intent.entities == {"ARTIFACT": "service", "LANGUAGE": "java"}
    expected = math.exp(4) / (math.exp(4) + 1 + math.exp(-1))
    assert intent.confidence.value == pytest.approx(expected)
    assert seen[0]["url"].endswith("/v1/models/intent:predict")
    assert seen[0]["body"] == {"instances": [{"tokens": [2, 3, 4, 5, 6, 0, 0, 0]}]}


def test_temperature_softens_the_distribution() -> None:
    sharp = TFServingIntentClassifier(
        _client([4.0, 0.0, -1.0], [0]), "intent", _meta(1.0)
    ).classify("make")
    soft = TFServingIntentClassifier(_client([4.0, 0.0, -1.0], [0]), "intent", _meta(3.0)).classify(
        "make"
    )
    assert soft.confidence.value < sharp.confidence.value


def test_unknown_words_map_to_unk_and_long_inputs_are_truncated() -> None:
    seen: list[dict] = []
    TFServingIntentClassifier(_client([1.0, 0.0, 0.0], [0], seen), "intent", _meta()).classify(
        "make zzz " + "a " * 20
    )
    ids = seen[0]["body"]["instances"][0]["tokens"]
    assert ids[:2] == [2, 1] and len(ids) == 8


def test_version_label_is_used_in_the_url() -> None:
    seen: list[dict] = []
    TFServingIntentClassifier(
        _client([1.0, 0.0, 0.0], [0], seen), "intent", _meta(), label="champion"
    ).classify("a")
    assert seen[0]["url"].endswith("/v1/models/intent/labels/champion:predict")


def test_server_errors_become_classification_errors() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(503)), base_url="http://tf"
    )
    with pytest.raises(ClassificationError):
        TFServingIntentClassifier(client, "intent", _meta()).classify("make a service")


def test_empty_text_is_rejected_without_calling_the_server() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise AssertionError("must not call")

    client = httpx.Client(transport=httpx.MockTransport(boom), base_url="http://tf")
    with pytest.raises(ClassificationError):
        TFServingIntentClassifier(client, "intent", _meta()).classify("???")


def test_model_meta_loads_from_an_exported_version_directory(tmp_path) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / "vocab.json").write_text(json.dumps(VOCAB))
    (tmp_path / "labels.json").write_text(
        json.dumps({"intents": INTENTS, "slot_tags": SLOTS, "max_len": 8})
    )
    (tmp_path / "temperature.json").write_text(json.dumps({"temperature": 1.7}))
    meta = ModelMeta.load(tmp_path)
    assert (meta.temperature, meta.max_len, meta.intents) == (1.7, 8, INTENTS)
