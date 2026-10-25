from collections.abc import Mapping

from app.application.errors import ClassificationError
from app.application.ports.intent_classifier import IntentClassifier
from app.domain.entities import Intent
from app.domain.value_objects import Confidence


class FakeClassifier(IntentClassifier):
    """Returns a canned intent (or raises) and records what it was asked."""

    def __init__(
        self,
        name: str = "CREATE_CODE_ARTIFACT",
        confidence: float = 0.95,
        entities: Mapping[str, str] | None = None,
        fail: bool = False,
    ) -> None:
        self._intent = Intent(name, Confidence(confidence), dict(entities or {}))
        self._fail = fail
        self.seen: list[str] = []

    def classify(self, text: str) -> Intent:
        self.seen.append(text)
        if self._fail:
            raise ClassificationError("down")
        return self._intent
