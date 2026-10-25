from collections import Counter

import pytest

from ml.training.common.datasets import load_taxonomy, read_jsonl, validate_record
from ml.training.intent.pipeline import (
    build_label_space,
    build_training_records,
    class_weights,
    split_train_val,
)

TAXONOMY = load_taxonomy()


def test_templates_expand_to_valid_records_with_a_capped_synthetic_share(ml_root) -> None:  # type: ignore[no-untyped-def]
    rows = build_training_records(ml_root, max_synthetic_share=0.4, seed=0)
    assert all(not validate_record(r, TAXONOMY) for r in rows)
    by_intent: dict[str, Counter] = {}
    for r in rows:
        by_intent.setdefault(r["intent"], Counter())[r["source"] == "template"] += 1
    for intent, counts in by_intent.items():
        share = counts[True] / (counts[True] + counts[False])
        assert 0 < share <= 0.4 + 1e-9, (intent, share)
    assert len({r["id"] for r in rows}) == len(rows)


def test_training_data_never_contains_golden_or_challenge_text(ml_root) -> None:  # type: ignore[no-untyped-def]
    from ml.training.common.datasets import record_text

    texts = {record_text(r) for r in build_training_records(ml_root, 0.4, 0)}
    for name in ("golden", "challenge"):
        assert not texts & {
            record_text(r) for r in read_jsonl(ml_root / f"data/golden/{name}.jsonl")
        }


def test_validation_split_is_disjoint_and_group_aware() -> None:
    rows = [{"id": f"u{i}", "intent": "A"} for i in range(40)] + [
        {"id": f"u{i}-asr1", "parent_id": f"u{i}", "intent": "A"} for i in range(40)
    ]
    train, val = split_train_val(rows, val_fraction=0.2, seed=3)
    assert not {r["id"] for r in train} & {r["id"] for r in val}
    parents_train = {r.get("parent_id", r["id"]) for r in train}
    assert not parents_train & {r.get("parent_id", r["id"]) for r in val}
    assert len(val) == pytest.approx(16, abs=4)


def test_label_space_is_sorted_and_complete() -> None:
    intents, tags = build_label_space(TAXONOMY)
    assert (
        intents == sorted(TAXONOMY["intents"])
        and tags[0] == "O"
        and len(tags) == 1 + 2 * len(TAXONOMY["entities"])
    )


def test_class_weights_upweight_rare_classes() -> None:
    w = class_weights(["A"] * 90 + ["B"] * 10, ["A", "B"])
    assert w["B"] > w["A"] and w["A"] * 90 + w["B"] * 10 == pytest.approx(100)
