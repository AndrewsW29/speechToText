"""Template expansion: phrasings x slot values, with a cap on the synthetic share."""

from __future__ import annotations

import itertools
import random
import re
from collections.abc import Mapping, Sequence
from typing import Any

from ml.training.common.markup import to_record

_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")


def max_rows_for_share(hand_written: int, max_share: float) -> int:
    """Largest synthetic count n with n / (hand_written + n) <= max_share."""
    if not 0 < max_share < 1:
        raise ValueError("max_share must be within (0, 1)")
    return int(max_share * hand_written / (1 - max_share) + 1e-9)


def _variants(template: str, slots: Mapping[str, Sequence[str]]) -> list[str]:
    parts = _PLACEHOLDER.split(template)  # text, placeholder, text, placeholder, ...
    choices: list[list[str]] = []
    for index, part in enumerate(parts):
        if index % 2 == 0:
            choices.append([part])
        elif "|" in part:
            choices.append(part.split("|"))
        else:
            choices.append([f"[{value}|{part}]" for value in slots[part]])
    return ["".join(combo) for combo in itertools.product(*choices)]


def expand(
    templates: Sequence[str],
    slots: Mapping[str, Sequence[str]],
    intent: str,
    max_rows: int | None,
    seed: int,
) -> list[dict[str, Any]]:
    markups = [m for template in templates for m in _variants(template, slots)]
    rows = [
        to_record(f"tpl-{intent.lower()}-{index:04d}", intent, markup, source="template")
        for index, markup in enumerate(markups)
    ]
    if max_rows is not None and max_rows < len(rows):
        keep = sorted(random.Random(seed).sample(range(len(rows)), max_rows))
        rows = [rows[i] for i in keep]
    return rows
