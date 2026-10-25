import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from ml.training.common.datasets import load_taxonomy, read_jsonl, record_text, validate_record

TAXONOMY = load_taxonomy()
FILES = {
    "raw/seed.jsonl": "seed",
    "golden/golden.jsonl": "golden",
    "golden/challenge.jsonl": "challenge",
}
MAX_DUPLICATE_RATE = 0.02


def test_taxonomy_is_small_mutually_exclusive_and_has_out_of_scope() -> None:
    intents = TAXONOMY["intents"]
    assert 8 <= len(intents) <= 12 and "OUT_OF_SCOPE" in intents
    assert len({v["handler"] for v in intents.values()}) == len(intents), "one handler per intent"
    assert set(TAXONOMY["entities"]) == {
        "LANGUAGE",
        "FRAMEWORK",
        "ARTIFACT",
        "LIBRARY",
        "VERSION",
        "ERROR_CODE",
    }


@pytest.mark.parametrize(("name", "source"), FILES.items())
def test_every_record_is_valid(ml_root: Path, name: str, source: str) -> None:
    rows = read_jsonl(ml_root / "data" / name)
    assert rows, f"{name} is empty"
    problems = {r["id"]: p for r in rows if (p := validate_record(r, TAXONOMY))}
    assert not problems, problems
    assert {r["source"] for r in rows} == {source}
    assert len({r["id"] for r in rows}) == len(rows), "duplicate ids"


@pytest.mark.parametrize(("name", "source"), FILES.items())
def test_duplicate_rate_is_low(ml_root: Path, name: str, source: str) -> None:
    texts = [record_text(r) for r in read_jsonl(ml_root / "data" / name)]
    assert 1 - len(set(texts)) / len(texts) <= MAX_DUPLICATE_RATE


def test_seed_has_at_least_fifty_utterances_per_intent(ml_root: Path) -> None:
    counts = Counter(r["intent"] for r in read_jsonl(ml_root / "data/raw/seed.jsonl"))
    assert set(counts) == set(TAXONOMY["intents"])
    assert min(counts.values()) >= 50 and max(counts.values()) <= 100, counts


def test_golden_set_is_balanced_and_the_right_size(ml_root: Path) -> None:
    rows = read_jsonl(ml_root / "data/golden/golden.jsonl")
    counts = Counter(r["intent"] for r in rows)
    assert len(rows) == 200 and min(counts.values()) >= 24, counts


def test_challenge_set_covers_noise_and_out_of_scope_hard_negatives(ml_root: Path) -> None:
    rows = read_jsonl(ml_root / "data/golden/challenge.jsonl")
    assert len(rows) >= 48 and sum(r["intent"] == "OUT_OF_SCOPE" for r in rows) >= 6


def test_golden_sets_are_frozen(ml_root: Path) -> None:
    expected = json.loads((ml_root / "data/golden/CHECKSUMS.json").read_text())
    for name, digest in expected.items():
        actual = hashlib.sha256((ml_root / "data/golden" / name).read_bytes()).hexdigest()
        assert actual == digest, (
            f"{name} changed; the golden sets are frozen (re-freeze deliberately)"
        )


def _good() -> dict:
    return {
        "id": "x",
        "tokens": ["a", "b"],
        "tags": ["O", "B-LANGUAGE"],
        "intent": "FIND_DOCS",
        "source": "seed",
    }


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        (lambda r: r.update(tags=["O"]), "differ in length"),
        (lambda r: r.update(tokens=["a", " "]), "empty tokens"),
        (lambda r: r.update(intent="NOPE"), "unknown intent"),
        (lambda r: r.update(tags=["O", "B-NOPE"]), "invalid tag"),
        (lambda r: r.update(tags=["I-LANGUAGE", "O"]), "does not continue"),
        (lambda r: r.pop("source"), "missing field"),
        (lambda r: r.update(source="asr_augmented"), "parent_id"),
    ],
)
def test_validator_catches_bad_records(mutate, fragment: str) -> None:  # type: ignore[no-untyped-def]
    record = _good()
    mutate(record)
    assert any(fragment in p for p in validate_record(record, TAXONOMY))


def test_validator_accepts_a_good_record() -> None:
    assert validate_record(_good(), TAXONOMY) == []
