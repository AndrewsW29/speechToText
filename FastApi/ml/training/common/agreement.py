from __future__ import annotations

from collections.abc import Sequence

from sklearn.metrics import cohen_kappa_score

TARGET_KAPPA = 0.8


def cohen_kappa(a: Sequence[str], b: Sequence[str]) -> float:
    if len(a) != len(b):
        raise ValueError("annotation lists must have the same length")
    return float(cohen_kappa_score(a, b))
