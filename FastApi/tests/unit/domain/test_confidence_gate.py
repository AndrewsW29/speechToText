import pytest
from app.domain.confidence_gate import ConfidenceGate, Decision
from app.domain.entities import Intent
from app.domain.value_objects import Confidence


def _intent(name: str = "EXPLAIN_CONCEPT", conf: float = 0.95, **entities: str) -> Intent:
    return Intent(name=name, confidence=Confidence(conf), entities=entities)


def test_confident_intent_with_required_entities_is_answered() -> None:
    assert (
        ConfidenceGate().decide(_intent("CREATE_CODE_ARTIFACT", 0.95, LANGUAGE="java"))
        is Decision.ANSWER
    )


def test_missing_required_language_asks_for_clarification() -> None:
    gate = ConfidenceGate()
    intent = _intent("CREATE_CODE_ARTIFACT", 0.95, ARTIFACT="controller")
    assert gate.decide(intent) is Decision.CLARIFY
    assert gate.missing_entities(intent) == frozenset({"LANGUAGE"})


def test_intents_without_required_entities_do_not_need_a_language() -> None:
    assert ConfidenceGate().decide(_intent("EXPLAIN_CONCEPT", 0.9)) is Decision.ANSWER


def test_medium_confidence_clarifies_and_low_confidence_abstains() -> None:
    gate = ConfidenceGate()
    assert gate.decide(_intent(conf=0.6)) is Decision.CLARIFY
    assert gate.decide(_intent(conf=0.3)) is Decision.ABSTAIN


@pytest.mark.parametrize(
    ("conf", "expected"),
    [
        (0.80, Decision.ANSWER),
        (0.7999, Decision.CLARIFY),
        (0.50, Decision.CLARIFY),
        (0.4999, Decision.ABSTAIN),
    ],
)
def test_threshold_boundaries(conf: float, expected: Decision) -> None:
    assert ConfidenceGate().decide(_intent(conf=conf)) is expected


def test_out_of_scope_always_abstains_even_when_confident() -> None:
    assert ConfidenceGate().decide(_intent("OUT_OF_SCOPE", 0.99)) is Decision.ABSTAIN


def test_custom_policy() -> None:
    gate = ConfidenceGate(
        answer_at=0.9, clarify_at=0.6, required={"FIND_DOCS": frozenset({"FRAMEWORK"})}
    )
    assert gate.decide(_intent("FIND_DOCS", 0.95)) is Decision.CLARIFY
    assert gate.decide(_intent("FIND_DOCS", 0.95, FRAMEWORK="spring")) is Decision.ANSWER
    assert gate.decide(_intent(conf=0.85)) is Decision.CLARIFY


def test_invalid_thresholds_are_rejected() -> None:
    with pytest.raises(ValueError):
        ConfidenceGate(answer_at=0.4, clarify_at=0.5)
