"""Evaluation metrics shared by every gate."""

from __future__ import annotations

import math
from collections.abc import Collection, Sequence

import jiwer
import numpy as np
from seqeval.metrics import f1_score as _seq_f1
from sklearn.metrics import f1_score


def macro_f1(y_true: Sequence[str], y_pred: Sequence[str]) -> float:
    return float(f1_score(y_true, y_pred, average="macro", zero_division=0))


def entity_f1(gold: Sequence[Sequence[str]], pred: Sequence[Sequence[str]]) -> float:
    return float(_seq_f1([list(g) for g in gold], [list(p) for p in pred], zero_division=0))


def ece(confidences: Sequence[float], correct: Sequence[bool], bins: int = 10) -> float:
    """Expected calibration error: bin-weighted gap between confidence and accuracy."""
    if len(confidences) != len(correct):
        raise ValueError("confidences and correct must have the same length")
    conf, hit = np.asarray(confidences, dtype=float), np.asarray(correct, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = 0.0
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        mask = (conf > low) & (conf <= high) if low > 0 else (conf >= low) & (conf <= high)
        if mask.any():
            total += abs(hit[mask].mean() - conf[mask].mean()) * mask.sum() / len(conf)
    return float(total)


def recall_at_k(
    ranked: Sequence[Sequence[str]], relevant: Sequence[Collection[str]], k: int
) -> float:
    """Share of queries with at least one relevant item in the top k."""
    pairs = list(zip(ranked, relevant, strict=True))
    hits = sum(any(item in rel for item in ranking[:k]) for ranking, rel in pairs)
    return hits / len(pairs)


def mrr_at_k(ranked: Sequence[Sequence[str]], relevant: Sequence[Collection[str]], k: int) -> float:
    total = 0.0
    pairs = list(zip(ranked, relevant, strict=True))
    for ranking, rel in pairs:
        for rank, item in enumerate(ranking[:k], start=1):
            if item in rel:
                total += 1.0 / rank
                break
    return total / len(pairs)


def ndcg_at_k(graded: Sequence[Sequence[float]], k: int) -> float:
    """Mean nDCG@k; each list holds graded relevance in the order the results were shown."""

    def dcg(values: Sequence[float]) -> float:
        return sum((2**rel - 1) / math.log2(i + 2) for i, rel in enumerate(values[:k]))

    scores = []
    for gains in graded:
        ideal = dcg(sorted(gains, reverse=True))
        scores.append(dcg(gains) / ideal if ideal > 0 else 0.0)
    return sum(scores) / len(scores)


def wer(references: Sequence[str], hypotheses: Sequence[str]) -> float:
    return float(jiwer.wer(list(references), list(hypotheses)))


def tter(references: Sequence[str], hypotheses: Sequence[str], glossary: Collection[str]) -> float:
    """Technical term error rate: share of glossary terms in the reference missing in the hypothesis."""
    total = missing = 0
    for ref, hyp in zip(references, hypotheses, strict=True):
        hyp_words = {w.strip(".,;:!?") for w in hyp.split()}
        for word in {w.strip(".,;:!?") for w in ref.split()}:
            if word in glossary:
                total += 1
                missing += word not in hyp_words
    return missing / total if total else float("nan")
