import numpy as np
import pytest

from ml.training.common.metrics import ece
from ml.training.intent.calibrate import apply_temperature, fit_temperature


def _logits(scale: float, n: int = 600, k: int = 5, accuracy: float = 0.7, seed: int = 0):  # type: ignore[no-untyped-def]
    """Logits whose argmax is right `accuracy` of the time, multiplied by `scale`."""
    rng = np.random.default_rng(seed)
    labels = rng.integers(0, k, size=n)
    logits = rng.normal(size=(n, k))
    right = rng.random(n) < accuracy
    logits[np.arange(n), np.where(right, labels, (labels + 1) % k)] += 3.0
    return logits * scale, labels


def _ece_of(logits: np.ndarray, labels: np.ndarray, temperature: float) -> float:
    probs = apply_temperature(logits, temperature)
    return ece(probs.max(axis=1), probs.argmax(axis=1) == labels)


def test_overconfident_logits_get_a_temperature_above_one_and_lower_ece() -> None:
    logits, labels = _logits(scale=4.0)
    t = fit_temperature(logits, labels)
    assert t > 1.5
    assert _ece_of(logits, labels, t) < _ece_of(logits, labels, 1.0)


def test_underconfident_logits_get_a_temperature_below_one() -> None:
    logits, labels = _logits(scale=0.3, accuracy=0.9)
    assert fit_temperature(logits, labels) < 1.0


def test_temperature_generalises_to_held_out_data() -> None:
    val_logits, val_labels = _logits(scale=4.0, seed=1)
    test_logits, test_labels = _logits(scale=4.0, seed=2)
    t = fit_temperature(val_logits, val_labels)  # fitted on validation only
    assert _ece_of(test_logits, test_labels, t) < _ece_of(test_logits, test_labels, 1.0)


def test_temperature_does_not_change_the_predicted_class() -> None:
    logits, _ = _logits(scale=2.0)
    assert (apply_temperature(logits, 3.0).argmax(1) == logits.argmax(1)).all()


def test_probabilities_sum_to_one_and_temperature_is_bounded() -> None:
    logits, labels = _logits(scale=2.0)
    assert apply_temperature(logits, 1.7).sum(axis=1) == pytest.approx(np.ones(len(logits)))
    assert 0.05 <= fit_temperature(logits, labels) <= 10.0


def test_inputs_are_validated() -> None:
    with pytest.raises(ValueError):
        fit_temperature(np.zeros((3, 2)), np.zeros(2, dtype=int))
    with pytest.raises(ValueError):
        apply_temperature(np.zeros((1, 2)), 0.0)
