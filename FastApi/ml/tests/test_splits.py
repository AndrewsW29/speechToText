import pytest

from ml.training.common.splits import group_split, time_split


def _records() -> list[dict]:
    out = []
    for i in range(40):
        out.append({"id": f"u{i}", "intent": "X"})
        for j in range(3):
            out.append({"id": f"u{i}-v{j}", "parent_id": f"u{i}", "intent": "X"})
    return out


def test_all_variants_of_a_parent_land_in_the_same_split() -> None:
    splits = group_split(_records(), {"train": 0.7, "val": 0.15, "test": 0.15}, seed=1)
    where = {}
    for name, rows in splits.items():
        for r in rows:
            parent = r.get("parent_id", r["id"])
            assert where.setdefault(parent, name) == name, (
                f"{parent} split across {where[parent]} and {name}"
            )
    assert sum(len(v) for v in splits.values()) == 160


def test_split_is_deterministic_for_a_seed_and_differs_across_seeds() -> None:
    a = group_split(_records(), {"train": 0.8, "val": 0.2}, seed=3)
    b = group_split(_records(), {"train": 0.8, "val": 0.2}, seed=3)
    c = group_split(_records(), {"train": 0.8, "val": 0.2}, seed=4)
    ids = lambda s: [r["id"] for r in s["train"]]  # noqa: E731
    assert ids(a) == ids(b) and ids(a) != ids(c)


def test_ratios_must_sum_to_one() -> None:
    with pytest.raises(ValueError):
        group_split(_records(), {"train": 0.5, "val": 0.2}, seed=0)


def test_time_split_trains_on_older_validates_on_newer() -> None:
    rows = [{"id": str(i), "week": f"2026-W{i:02d}"} for i in range(1, 11)]
    train, val = time_split(rows, key="week", val_fraction=0.3)
    assert max(r["week"] for r in train) < min(r["week"] for r in val)
    assert len(val) == 3
