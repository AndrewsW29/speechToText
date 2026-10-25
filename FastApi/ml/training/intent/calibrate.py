"""Temperature scaling: one scalar fitted on held-out validation logits only."""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import log_softmax, softmax

MIN_T, MAX_T = 0.05, 10.0


def apply_temperature(logits: np.ndarray, temperature: float) -> np.ndarray:
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    return np.asarray(softmax(np.asarray(logits, dtype=float) / temperature, axis=-1))


def fit_temperature(val_logits: np.ndarray, val_labels: np.ndarray) -> float:
    """Minimise the negative log-likelihood of the validation set over a scalar temperature."""
    logits, labels = np.asarray(val_logits, dtype=float), np.asarray(val_labels, dtype=int)
    if logits.ndim != 2 or len(logits) != len(labels):
        raise ValueError("need (n, classes) logits and n labels")

    def nll(t: float) -> float:
        return float(-log_softmax(logits / t, axis=1)[np.arange(len(labels)), labels].mean())

    return float(minimize_scalar(nll, bounds=(MIN_T, MAX_T), method="bounded").x)
