"""The frozen golden/challenge sets must never overlap with anything used for training."""

from pathlib import Path

from ml.training.common.datasets import normalize, read_jsonl, record_text

TRAIN_FILES = (
    "raw/seed.jsonl",
    "interim/template.jsonl",
    "interim/paraphrase.jsonl",
    "interim/asr_augmented.jsonl",
    "processed/train.jsonl",
)


def _texts(path: Path) -> set[str]:
    return {record_text(r) for r in read_jsonl(path)} if path.exists() else set()


def test_golden_set_has_no_overlap_with_training_data(ml_root: Path) -> None:
    golden = _texts(ml_root / "data/golden/golden.jsonl")
    assert golden, "golden set is missing"
    for name in TRAIN_FILES:
        assert not (golden & _texts(ml_root / "data" / name)), f"golden leaks into {name}"


def test_challenge_set_has_no_overlap_with_training_data(ml_root: Path) -> None:
    challenge = _texts(ml_root / "data/golden/challenge.jsonl")
    assert challenge, "challenge set is missing"
    for name in TRAIN_FILES:
        assert not (challenge & _texts(ml_root / "data" / name)), f"challenge leaks into {name}"


def test_golden_and_challenge_do_not_overlap_each_other(ml_root: Path) -> None:
    assert not (
        _texts(ml_root / "data/golden/golden.jsonl")
        & _texts(ml_root / "data/golden/challenge.jsonl")
    )


def test_normalize_ignores_case_and_punctuation() -> None:
    assert normalize("How do I, create A Service?") == normalize("how do i create a service")
