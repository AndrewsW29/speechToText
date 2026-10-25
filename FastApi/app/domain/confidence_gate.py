"""Business rule: answer, ask for clarification, or abstain. Pure domain logic (no ML imports)."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

from app.domain.entities import Intent

OUT_OF_SCOPE = "OUT_OF_SCOPE"
DEFAULT_REQUIRED: Mapping[str, frozenset[str]] = {"CREATE_CODE_ARTIFACT": frozenset({"LANGUAGE"})}


class Decision(StrEnum):
    ANSWER = "answer"
    CLARIFY = "clarify"
    ABSTAIN = "abstain"


class ConfidenceGate:
    """A wrong confident answer is worse than a question or an honest "I don't know"."""

    def __init__(
        self,
        answer_at: float = 0.80,
        clarify_at: float = 0.50,
        required: Mapping[str, frozenset[str]] | None = None,
    ) -> None:
        if not 0.0 <= clarify_at <= answer_at <= 1.0:
            raise ValueError("need 0 <= clarify_at <= answer_at <= 1")
        self._answer_at = answer_at
        self._clarify_at = clarify_at
        self._required = dict(DEFAULT_REQUIRED if required is None else required)

    def missing_entities(self, intent: Intent) -> frozenset[str]:
        return self._required.get(intent.name, frozenset()) - intent.entities.keys()

    def decide(self, intent: Intent) -> Decision:
        confidence = intent.confidence.value
        if intent.name == OUT_OF_SCOPE or confidence < self._clarify_at:
            return Decision.ABSTAIN
        if confidence < self._answer_at or self.missing_entities(intent):
            return Decision.CLARIFY
        return Decision.ANSWER
