"""Near-duplicate detection by cosine similarity (TF-IDF by default, any embedder optional)."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

Embed = Callable[[Sequence[str]], Sequence[Sequence[float]]]


def _tfidf(texts: Sequence[str]) -> np.ndarray:
    return np.asarray(TfidfVectorizer().fit_transform(texts).todense())


def near_duplicates(
    texts: Sequence[str], threshold: float, embed: Embed | None = None
) -> set[tuple[int, int]]:
    matrix = np.asarray(embed(texts) if embed else _tfidf(texts), dtype=float)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    unit = matrix / np.where(norms == 0, 1, norms)
    sims = unit @ unit.T
    n = len(texts)
    return {(i, j) for i in range(n) for j in range(i + 1, n) if sims[i, j] >= threshold}


def remove_near_duplicates(
    texts: Sequence[str], threshold: float, embed: Embed | None = None
) -> list[int]:
    """Indices to keep: the first member of every near-duplicate cluster."""
    dupes = near_duplicates(texts, threshold, embed)
    kept: list[int] = []
    for j in range(len(texts)):
        if not any((i, j) in dupes for i in kept):
            kept.append(j)
    return kept
