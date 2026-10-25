"""Out-of-scope detection: three independent defences, reported in a fixed order."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

OUT_OF_SCOPE = "OUT_OF_SCOPE"


@dataclass(frozen=True, slots=True)
class OodVerdict:
    rejected: bool
    reason: str | None


def is_out_of_scope(
    probabilities: Sequence[float],
    classes: Sequence[str],
    confidence_threshold: float = 0.5,
    retrieval_score: float | None = None,
    retrieval_threshold: float | None = None,
) -> OodVerdict:
    """1) the explicit OUT_OF_SCOPE class, 2) low calibrated confidence, 3) no retrieval support."""
    best = max(range(len(probabilities)), key=probabilities.__getitem__)
    if classes[best] == OUT_OF_SCOPE:
        return OodVerdict(True, "class")
    if probabilities[best] < confidence_threshold:
        return OodVerdict(True, "low_confidence")
    if (
        retrieval_score is not None
        and retrieval_threshold is not None
        and retrieval_score < retrieval_threshold
    ):
        return OodVerdict(True, "no_retrieval_support")
    return OodVerdict(False, None)
