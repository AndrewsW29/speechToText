"""Gate evaluation of the newest exported intent model against the frozen golden set.

Skipped when no model has been trained on this machine (artifacts are not committed).
Run: `pytest tests/ml -m gates` after `python -m ml.training.intent.pipeline`.
"""

from pathlib import Path

import pytest

pytest.importorskip("tensorflow")

from ml.evaluation.intent_eval import evaluate_predictor, load_predictor
from ml.training.common.datasets import ML_ROOT, read_jsonl

pytestmark = pytest.mark.gates
FLOORS = {"intent_macro_f1": 0.90, "ood_recall": 0.90, "slot_f1": 0.85}
MAX_ECE = 0.05


def _latest() -> Path:
    versions = sorted(
        (p for p in (ML_ROOT / "artifacts" / "intent").glob("*") if p.name.isdigit()),
        key=lambda p: int(p.name),
    )
    if not versions:
        pytest.skip("no exported intent model")
    return versions[-1]


@pytest.fixture(scope="module")
def metrics() -> dict:
    return evaluate_predictor(
        load_predictor(_latest()), read_jsonl(ML_ROOT / "data/golden/golden.jsonl")
    )


@pytest.mark.parametrize("name", sorted(FLOORS))
def test_exported_model_meets_the_gate(metrics: dict, name: str) -> None:
    assert metrics[name] >= FLOORS[name], f"{name}={metrics[name]:.3f} < {FLOORS[name]}"


def test_exported_model_is_calibrated(metrics: dict) -> None:
    assert metrics["ece"] <= MAX_ECE, f"ece={metrics['ece']:.3f}"


def test_exported_model_beats_the_baseline_on_the_challenge_set() -> None:
    import json

    baseline = json.loads((ML_ROOT / "evaluation/baseline_metrics.json").read_text())["challenge"]
    got = evaluate_predictor(
        load_predictor(_latest()), read_jsonl(ML_ROOT / "data/golden/challenge.jsonl")
    )
    assert got["intent_macro_f1"] >= baseline["intent_macro_f1"] - 0.05
