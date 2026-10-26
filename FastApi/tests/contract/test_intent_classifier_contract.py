"""Contract every IntentClassifier adapter must satisfy (Liskov)."""

from collections.abc import Callable

import httpx
import pytest
from app.adapters.outbound.intent.tf_serving_classifier import (
    ModelMeta,
    TFServingIntentClassifier,
)
from app.application.errors import ClassificationError
from app.application.ports.intent_classifier import IntentClassifier
from app.domain.entities import Intent

from tests.fakes import FakeClassifier

META = ModelMeta(
    vocab={"<pad>": 0, "<unk>": 1, "make": 2, "a": 3, "spring": 4, "service": 5},
    intents=["CREATE_CODE_ARTIFACT", "OUT_OF_SCOPE"],
    slot_tags=["O", "B-FRAMEWORK"],
    temperature=1.0,
    max_len=8,
)


def _tf_serving(fail: bool = False) -> IntentClassifier:
    def handler(request: httpx.Request) -> httpx.Response:
        if fail:
            return httpx.Response(503)
        row = {"intent": [3.0, 0.0], "slots": [[1.0, 0.0]] * 8}
        row["slots"][2] = [0.0, 5.0]  # "spring"
        return httpx.Response(200, json={"predictions": [row]})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://tf")
    return TFServingIntentClassifier(client, "intent", META)


FACTORIES: dict[str, Callable[[bool], IntentClassifier]] = {
    "fake": lambda fail: FakeClassifier(fail=fail),
    "tf-serving": _tf_serving,
}


@pytest.fixture(params=list(FACTORIES), ids=list(FACTORIES))
def make(request: pytest.FixtureRequest) -> Callable[[bool], IntentClassifier]:
    return FACTORIES[request.param]


def test_returns_an_intent_with_confidence_in_range(
    make: Callable[[bool], IntentClassifier],
) -> None:
    result = make(False).classify("make a spring service")
    assert isinstance(result, Intent)
    assert result.name
    assert 0.0 <= result.confidence.value <= 1.0


def test_entities_are_a_string_mapping(make: Callable[[bool], IntentClassifier]) -> None:
    entities = make(False).classify("make a spring service").entities
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in entities.items())


def test_unavailable_model_raises_classification_error(
    make: Callable[[bool], IntentClassifier],
) -> None:
    with pytest.raises(ClassificationError):
        make(True).classify("make a spring service")
