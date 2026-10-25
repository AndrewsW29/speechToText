import math

import pytest

from ml.training.common.metrics import (
    ece,
    entity_f1,
    macro_f1,
    mrr_at_k,
    ndcg_at_k,
    recall_at_k,
    tter,
    wer,
)


def test_macro_f1_penalises_ignoring_a_rare_class() -> None:
    y_true = ["A"] * 9 + ["B"]
    assert macro_f1(y_true, ["A"] * 10) < 0.6  # accuracy would be 0.9
    assert macro_f1(y_true, y_true) == 1.0


def test_entity_f1_uses_span_level_matching() -> None:
    gold = [["O", "B-ARTIFACT", "I-ARTIFACT", "O"]]
    assert entity_f1(gold, gold) == 1.0
    assert entity_f1(gold, [["O", "B-ARTIFACT", "O", "O"]]) == 0.0  # partial span is wrong


def test_ece_zero_when_perfectly_calibrated_and_large_when_overconfident() -> None:
    assert ece([1.0] * 4, [True] * 4) == 0.0
    assert ece([0.99] * 10, [True] * 5 + [False] * 5) == pytest.approx(0.49, abs=0.01)


def test_ece_validates_inputs() -> None:
    with pytest.raises(ValueError):
        ece([0.5], [True, False])


def test_recall_mrr_ndcg() -> None:
    ranked = [["a", "b", "c"], ["x", "y", "z"]]
    relevant = [{"b"}, {"q"}]
    assert recall_at_k(ranked, relevant, 2) == 0.5
    assert mrr_at_k(ranked, relevant, 10) == pytest.approx(0.25)
    assert ndcg_at_k([[2, 1, 0]], 5) == pytest.approx(1.0)  # already ideal
    assert ndcg_at_k([[0, 1, 2]], 5) < 1.0
    assert ndcg_at_k([[0, 0, 0]], 5) == 0.0


def test_wer() -> None:
    assert wer(["create a service"], ["create a service"]) == 0.0
    assert wer(["create a service"], ["create a surface"]) == pytest.approx(1 / 3)


def test_tter_counts_missing_glossary_terms_only() -> None:
    glossary = {"@RestController", "JPA", "Kotlin"}
    refs = ["use @RestController with JPA", "learn Kotlin"]
    hyps = ["use rest controller with JPA", "learn Kotlin"]
    assert tter(refs, hyps, glossary) == pytest.approx(1 / 3)
    assert math.isnan(tter(["no terms here"], ["no terms here"], glossary))
