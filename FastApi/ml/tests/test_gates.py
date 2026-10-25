"""Quality gates for a candidate model. Marked `gates`: they FAIL (red) until US10 delivers a model.

Run them with `pytest ml/tests/test_gates.py -m gates`; the default test run deselects them.
"""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.gates

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "artifacts" / "candidate" / "metrics.json"
CHAMPION = ROOT / "artifacts" / "champion" / "metrics.json"

GATES = {  # starting floors; replace with measured baselines (see evaluation/gates.yaml)
    "intent_macro_f1": 0.90,
    "slot_f1": 0.85,
    "ood_recall": 0.90,
}
RETRIEVAL_GATES = {"recall_at_5": 0.85}  # delivered by US11
MAX_ECE = 0.05
MAX_SLICE_REGRESSION = 0.01


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def test_candidate_meets_quality_gates() -> None:
    metrics = load(CANDIDATE)
    for name, floor in GATES.items():
        assert metrics[name] >= floor, f"{name}={metrics[name]:.3f} is below {floor}"
    assert metrics["ece"] <= MAX_ECE, f"ece={metrics['ece']:.3f} is above {MAX_ECE}"


def test_candidate_beats_the_tfidf_baseline() -> None:
    baseline = load(ROOT / "evaluation" / "baseline_metrics.json")["golden"]
    metrics = load(CANDIDATE)
    assert metrics["intent_macro_f1"] > baseline["intent_macro_f1"]
    assert metrics["ood_recall"] > baseline["ood_recall"]


def test_retrieval_gates() -> None:
    metrics = load(ROOT / "artifacts" / "candidate" / "retrieval_metrics.json")
    for name, floor in RETRIEVAL_GATES.items():
        assert metrics[name] >= floor, f"{name}={metrics[name]:.3f} is below {floor}"


def test_no_slice_regresses_against_champion() -> None:
    if not CHAMPION.exists():
        pytest.skip("no champion yet: the first promoted model becomes the champion (US13)")
    candidate = load(CANDIDATE)["slices"]
    champion = load(CHAMPION)["slices"]
    for name, champion_f1 in champion.items():
        assert candidate[name] >= champion_f1 - MAX_SLICE_REGRESSION, f"slice '{name}' regressed"
