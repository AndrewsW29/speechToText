"""Group-aware splits: variants of one utterance never straddle train/val/test."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from typing import Any

Record = dict[str, Any]


def _group(record: Record) -> str:
    return str(record.get("parent_id", record["id"]))


def group_split(
    records: Sequence[Record], ratios: Mapping[str, float], seed: int
) -> dict[str, list[Record]]:
    if abs(sum(ratios.values()) - 1.0) > 1e-6:
        raise ValueError("split ratios must sum to 1")
    groups: dict[str, list[Record]] = {}
    for record in records:
        groups.setdefault(_group(record), []).append(record)
    keys = sorted(groups)
    random.Random(seed).shuffle(keys)

    names = list(ratios)
    out: dict[str, list[Record]] = {name: [] for name in names}
    boundaries, acc = [], 0.0
    for name in names:
        acc += ratios[name]
        boundaries.append(round(acc * len(keys)))
    start = 0
    for name, end in zip(names, boundaries, strict=True):
        for key in keys[start:end]:
            out[name].extend(groups[key])
        start = end
    return out


def time_split(
    records: Sequence[Record], key: str, val_fraction: float
) -> tuple[list[Record], list[Record]]:
    """Train on older records, validate on newer ones (honest drift estimate)."""
    ordered = sorted(records, key=lambda r: r[key])
    n_val = round(len(ordered) * val_fraction)
    return ordered[: len(ordered) - n_val], ordered[len(ordered) - n_val :]
